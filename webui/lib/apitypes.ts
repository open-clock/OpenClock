import { ClockType } from "./clocktype";

export interface StatusResponse {
    setup: boolean;
    model: ClockType;
}

export interface CommandOutput {
    status: string
    output: string
    error: string
}