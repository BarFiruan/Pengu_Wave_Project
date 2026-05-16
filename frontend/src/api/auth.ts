import { apiFetch } from "./client";
import type { User } from "../types";

export async function login(email: string, password: string): Promise<{ user: User }> {
  return apiFetch("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export async function logout(): Promise<{ message: string }> {
  return apiFetch("/api/auth/logout", { method: "POST" });
}

export async function getMe(): Promise<User> {
  return apiFetch("/api/auth/me");
}
