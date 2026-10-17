import { client } from "./client";
import type { LoginPayload, LoginResult, RegisterPayload, User } from "./types";

export async function register(payload: RegisterPayload): Promise<User> {
  const { data } = await client.post<User>("/auth/register", payload);
  return data;
}

export async function login(payload: LoginPayload): Promise<LoginResult> {
  const { data } = await client.post<{ access_token: string; user: User }>("/auth/login", payload);
  return { token: data.access_token, user: data.user };
}

export async function getMe(): Promise<User> {
  const { data } = await client.get<User>("/auth/me");
  return data;
}
