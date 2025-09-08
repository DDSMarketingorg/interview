import aiohttp
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from urllib.parse import urljoin

from ..models.models import Lead, QualificationData, AppointmentRequest

logger = logging.getLogger(__name__)


class GHLService:
    """GoHighLevel API client"""

    def __init__(self, api_key: str, base_url: str = "https://services.leadconnectorhq.com"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    async def get_contact(self, contact_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve contact details from GHL"""
        try:
            url = urljoin(self.base_url, f"/contacts/{contact_id}")

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("contact")
                    else:
                        logger.error(
                            f"Failed to get contact {contact_id}: {response.status}")
                        return None

        except Exception as e:
            logger.error(f"Error retrieving contact {contact_id}: {e}")
            return None

    async def update_contact_notes(self, contact_id: str, notes: str,
                                   qualification_data: QualificationData) -> bool:
        """Update contact with call notes and qualification data"""
        try:
            # Prepare structured notes
            formatted_notes = self._format_qualification_notes(
                notes, qualification_data)

            # Prepare update payload
            update_data = {
                "notes": formatted_notes,
                "customFields": self._create_custom_fields(qualification_data)
            }

            url = urljoin(self.base_url, f"/contacts/{contact_id}")

            async with aiohttp.ClientSession() as session:
                async with session.put(
                    url,
                    headers=self.headers,
                    json=update_data
                ) as response:
                    if response.status == 200:
                        logger.info(
                            f"Successfully updated contact {contact_id}")
                        return True
                    else:
                        logger.error(
                            f"Failed to update contact {contact_id}: {response.status}")
                        response_text = await response.text()
                        logger.error(f"Response: {response_text}")
                        return False

        except Exception as e:
            logger.error(f"Error updating contact {contact_id}: {e}")
            return False

    async def update_contact_stage(self, contact_id: str, pipeline_id: str,
                                   stage_id: str) -> bool:
        """Move contact to a specific pipeline stage"""
        try:
            update_data = {
                "pipelineId": pipeline_id,
                "stageId": stage_id
            }

            url = urljoin(self.base_url, f"/contacts/{contact_id}/pipeline")

            async with aiohttp.ClientSession() as session:
                async with session.put(
                    url,
                    headers=self.headers,
                    json=update_data
                ) as response:
                    if response.status == 200:
                        logger.info(
                            f"Successfully moved contact {contact_id} to stage {stage_id}")
                        return True
                    else:
                        logger.error(
                            f"Failed to update contact stage {contact_id}: {response.status}")
                        return False

        except Exception as e:
            logger.error(f"Error updating contact stage {contact_id}: {e}")
            return False

    async def create_appointment(self, appointment_request: AppointmentRequest) -> Optional[str]:
        """Create an appointment in GHL calendar"""
        try:
            # Prepare appointment data
            appointment_data = {
                "contactId": appointment_request.contact_id,
                "startTime": appointment_request.appointment_date.isoformat(),
                "endTime": (appointment_request.appointment_date + timedelta(hours=1)).isoformat(),
                "title": f"Dental Consultation - {appointment_request.service_type}",
                "appointmentStatus": "confirmed",
                "notes": appointment_request.notes or "",
                "assignedUserId": None,  # Will be assigned by default calendar logic
            }

            url = urljoin(self.base_url, "/appointments")

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    headers=self.headers,
                    json=appointment_data
                ) as response:
                    if response.status == 201:
                        data = await response.json()
                        appointment_id = data.get("appointment", {}).get("id")
                        logger.info(
                            f"Successfully created appointment {appointment_id} for contact {appointment_request.contact_id}")
                        return appointment_id
                    else:
                        logger.error(
                            f"Failed to create appointment: {response.status}")
                        response_text = await response.text()
                        logger.error(f"Response: {response_text}")
                        return None

        except Exception as e:
            logger.error(f"Error creating appointment: {e}")
            return None

    async def add_contact_tag(self, contact_id: str, tag: str) -> bool:
        """Add a tag to a contact"""
        try:
            tag_data = {
                "tags": [tag]
            }

            url = urljoin(self.base_url, f"/contacts/{contact_id}/tags")

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    headers=self.headers,
                    json=tag_data
                ) as response:
                    if response.status == 200:
                        logger.info(
                            f"Successfully added tag '{tag}' to contact {contact_id}")
                        return True
                    else:
                        logger.error(
                            f"Failed to add tag to contact {contact_id}: {response.status}")
                        return False

        except Exception as e:
            logger.error(f"Error adding tag to contact {contact_id}: {e}")
            return False

    async def create_task(self, contact_id: str, title: str, description: str,
                          due_date: Optional[datetime] = None) -> Optional[str]:
        """Create a follow-up task for a contact"""
        try:
            task_data = {
                "contactId": contact_id,
                "title": title,
                "body": description,
                "dueDate": due_date.isoformat() if due_date else None,
                "completed": False
            }

            url = urljoin(self.base_url, "/tasks")

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    headers=self.headers,
                    json=task_data
                ) as response:
                    if response.status == 201:
                        data = await response.json()
                        task_id = data.get("task", {}).get("id")
                        logger.info(
                            f"Successfully created task {task_id} for contact {contact_id}")
                        return task_id
                    else:
                        logger.error(
                            f"Failed to create task: {response.status}")
                        return None

        except Exception as e:
            logger.error(f"Error creating task: {e}")
            return None

    def _format_qualification_notes(self, call_notes: str,
                                    qualification_data: QualificationData) -> str:
        """Format qualification data into structured notes"""
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

        notes = f"""
AI QUALIFICATION CALL - {timestamp}

CALL SUMMARY:
{call_notes}

QUALIFICATION DATA:
• Chief Complaint: {qualification_data.chief_complaint or 'Not specified'}
• Pain Level: {qualification_data.pain_level or 'Not assessed'}
• Urgency: {qualification_data.urgency}
• Insurance: {qualification_data.insurance_provider or 'Not provided'}
• Preferred Appointment: {qualification_data.preferred_appointment_time or 'Flexible'}
• Last Dental Visit: {qualification_data.last_dental_visit or 'Not discussed'}

NEXT STEPS:
"""

        if qualification_data.urgency == "emergency":
            notes += "• URGENT: Immediate follow-up required\n"
        elif qualification_data.urgency == "high":
            notes += "• Priority scheduling within 48 hours\n"
        else:
            notes += "• Standard appointment scheduling\n"

        if qualification_data.emergency_indicators:
            notes += f"• Emergency indicators noted: {', '.join(qualification_data.emergency_indicators)}\n"

        return notes.strip()

    def _create_custom_fields(self, qualification_data: QualificationData) -> List[Dict[str, Any]]:
        """Create custom field updates for qualification data"""
        custom_fields = []

        field_mappings = {
            "ai_pain_level": qualification_data.pain_level,
            "ai_urgency": qualification_data.urgency,
            "ai_insurance": qualification_data.insurance_provider,
            "ai_chief_complaint": qualification_data.chief_complaint,
            "ai_preferred_time": qualification_data.preferred_appointment_time,
            "ai_last_call": datetime.utcnow().isoformat()
        }

        for field_key, value in field_mappings.items():
            if value:
                custom_fields.append({
                    "key": field_key,
                    "value": str(value)
                })

        return custom_fields

    async def get_pipeline_stages(self, pipeline_id: str) -> List[Dict[str, Any]]:
        """Get available stages for a pipeline"""
        try:
            url = urljoin(self.base_url, f"/pipelines/{pipeline_id}/stages")

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("stages", [])
                    else:
                        logger.error(
                            f"Failed to get pipeline stages: {response.status}")
                        return []

        except Exception as e:
            logger.error(f"Error getting pipeline stages: {e}")
            return []

    async def process_qualification_results(self, lead_id: str,
                                            qualification_data: QualificationData,
                                            call_summary: str) -> Dict[str, Any]:
        """Process qualification results and update GHL accordingly"""
        results = {
            "contact_updated": False,
            "appointment_created": False,
            "stage_updated": False,
            "tags_added": [],
            "tasks_created": []
        }

        try:
            notes_updated = await self.update_contact_notes(
                lead_id,
                call_summary,
                qualification_data
            )
            results["contact_updated"] = notes_updated

            urgency_tag = f"AI-Qualified-{qualification_data.urgency.title()}"
            tag_added = await self.add_contact_tag(lead_id, urgency_tag)
            if tag_added:
                results["tags_added"].append(urgency_tag)

            if qualification_data.pain_level in ["severe", "emergency"]:
                pain_tag = f"Pain-Level-{qualification_data.pain_level.title()}"
                pain_tag_added = await self.add_contact_tag(lead_id, pain_tag)
                if pain_tag_added:
                    results["tags_added"].append(pain_tag)

            if (qualification_data.chief_complaint and
                qualification_data.preferred_appointment_time and
                    qualification_data.urgency != "emergency"):

                try:
                    appointment_date = datetime.utcnow() + timedelta(days=1)

                    appointment_request = AppointmentRequest(
                        contact_id=lead_id,
                        appointment_date=appointment_date,
                        service_type="Initial Consultation",
                        notes=f"AI Qualified - {qualification_data.chief_complaint}"
                    )

                    appointment_id = await self.create_appointment(appointment_request)
                    results["appointment_created"] = bool(appointment_id)

                except Exception as e:
                    logger.error(f"Error creating appointment: {e}")

            if qualification_data.urgency in ["high", "emergency"]:
                task_title = f"URGENT: Follow up AI qualified lead - {qualification_data.urgency}"
                task_description = f"""
AI Qualification completed with {qualification_data.urgency} urgency.
Chief complaint: {qualification_data.chief_complaint}
Pain level: {qualification_data.pain_level}
Immediate attention required.
"""

                task_id = await self.create_task(
                    lead_id,
                    task_title,
                    task_description,
                    datetime.utcnow() + timedelta(hours=2)
                )

                if task_id:
                    results["tasks_created"].append(task_id)

            logger.info(
                f"Qualification processing completed for {lead_id}: {results}")
            return results

        except Exception as e:
            logger.error(
                f"Error processing qualification results for {lead_id}: {e}")
            return results
