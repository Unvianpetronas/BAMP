// Base URL of the local FastAPI backend. Core features never call anything else (BR-08).
export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
