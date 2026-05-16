import { apiFetch } from "./client";
import type { User } from "../types";

export async function getUsers(): Promise<User[]> {
  return apiFetch("/api/users");
}

export async function createUser(body: {
  email: string;
  password: string;
  role: string;
}): Promise<User> {
  return apiFetch("/api/users", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function deleteUser(id: string): Promise<{ message: string }> {
  return apiFetch(`/api/users/${id}`, { method: "DELETE" });
}
