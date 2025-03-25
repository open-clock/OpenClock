import { ClockType } from "./clocktype";

export interface StatusResponse {
    setup: boolean;
    model: ClockType;
    wallmounted: boolean;
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

export interface Config {
    model: string;
    setup: boolean;
    wallmounted: boolean;
    debug: boolean;
    hostname: string;
    timezone: string;
}

export interface MicrosoftLoginResponse {
    verification_uri: string;
    user_code: string;
    message: string;
    expires_at: number;
}

export interface UntisLoginNameResponse {
    username: string;
}

export interface MicrosoftGetAccountsResponse {
    home_account_id: string,
    environment: string,
    username: string,
    account_source: string,
    authority_type: string,
    local_account_id: string,
    realm: string
}