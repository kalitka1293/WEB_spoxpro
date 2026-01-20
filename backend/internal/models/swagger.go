package models

// LoginResponse represents the response for the login endpoint
type LoginResponse struct {
	Message string `json:"message" example:"logged in"`
	UserID  string `json:"user" example:"550e8400-e29b-41d4-a716-446655440000"`
	JWT     string `json:"jwt" example:"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."`
}

// RegisterResponse represents the response for the register endpoint
type RegisterResponse struct {
	Message string `json:"message" example:"user registered"`
}

// ErrorResponse represents an error response
type ErrorResponse struct {
	Error string `json:"error" example:"invalid credentials"`
}