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

export interface Network {
    ssid: string;
    strength: number;
    connected: boolean;
    id: string;
}

export interface ConnectNetwork {
    ssid: string;
    password: string;
}