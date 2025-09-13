import { HighLevel } from '@gohighlevel/api-client';
import { AppointmentCreateSchema, AppointmentSchemaResponse } from '@gohighlevel/api-client/dist/lib/code/calendars/models/calendars';

type GHLResponse<T = any> = {
    success: boolean;
    data?: T;
    error?: string;
    message?: string;
}


// Appointment Management Tools
export class AppointmentManager {
    constructor(private client: HighLevel) { }

    /**
     * Create a new appointment
     */
    async createAppointment(appointmentData: Omit<AppointmentCreateSchema, 'id'>): Promise<GHLResponse<AppointmentSchemaResponse>> {
        try {
            const highLevelClient = this.client;
            const response = await highLevelClient.calendars.createAppointment(appointmentData);

            return {
                success: true,
                data: response
            };
        } catch (error: any) {
            return {
                success: false,
                error: error.message || 'Failed to create appointment'
            };
        }
    }

    /**
     * Update an existing appointment
     */
    async updateAppointment(appointmentId: string, updateData: Partial<AppointmentSchemaResponse>): Promise<GHLResponse<AppointmentSchemaResponse>> {
        try {
            const highLevelClient = this.client;
            const response = await highLevelClient.calendars.editAppointment(
                { eventId: appointmentId },
                {
                    title: updateData.title || '',
                    startTime: updateData.startTime,
                    endTime: updateData.endTime,
                    appointmentStatus: updateData.appointmentStatus,
                }
            );

            return {
                success: true,
                data: response
            };
        } catch (error: any) {
            return {
                success: false,
                error: error.message || 'Failed to update appointment'
            };
        }
    }
}
