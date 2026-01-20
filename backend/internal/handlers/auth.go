package handlers

import (
	"net/http"
	"strings"

	"github.com/YoungGoofy/shopping/backend/internal/models"
	"github.com/YoungGoofy/shopping/backend/internal/utils"
	"github.com/gin-gonic/gin"
	"github.com/golang-jwt/jwt/v5"
	"github.com/google/uuid"
	"github.com/patrickmn/go-cache"
	"github.com/sirupsen/logrus"
)

type LoginRequest struct {
	Email    string `json:"email"`
	Password string `json:"password"`
}

// LoginHandler godoc
// @Summary Login user
// @Description Login user with credentials and receive JWT token
// @Tags auth
// @Accept json
// @Produce json
// @Param request body LoginRequest true "Login credentials"
// @Success 200 {object} models.LoginResponse "Login successful"
// @Failure 400 {object} models.ErrorResponse "Invalid request"
// @Failure 401 {object} models.ErrorResponse "Invalid credentials"
// @Failure 500 {object} models.ErrorResponse "Internal server error"
// @Router /api/auth/login [post]
func (h Handler) LoginHandler(c *gin.Context) {
    var loginRequest LoginRequest
    if err := c.ShouldBindJSON(&loginRequest); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": "invalid request"})
        return
    }

    var user *models.User
    cachedUser, exists := h.cache.Get(loginRequest.Email)
    if exists {
        user = cachedUser.(*models.User)
    } else {
        
        dbUser, err := h.psql.GetUser(loginRequest.Email)
        if err != nil {
            c.JSON(http.StatusUnauthorized, gin.H{"error": "invalid credentials"})
            return
        }
        user = &dbUser
        h.cache.Set(loginRequest.Email, user, cache.DefaultExpiration)
    }

    if !utils.CheckPasswordHash(loginRequest.Password, user.Password) {
        c.JSON(http.StatusUnauthorized, gin.H{"error": "invalid credentials"})
        return
    }

    tokenString, err := h.jwt.GenerateToken(user)
    if err != nil {
        c.JSON(http.StatusInternalServerError, gin.H{"error": "internal error"})
        return
    }

    go h.redis.AddJWT(user.ID, tokenString)

    c.JSON(http.StatusOK, gin.H{
        "message": "logged in",
        "user":    user.ID,
        "jwt":     tokenString,
    })
}

type RegisterRequest struct {
	Name      string `json:"name"`
	LastName  string `json:"last_name"`
	Country   string `json:"country"`
	Phone     uint64 `json:"phone"`
	Email     string `json:"email"`
	Address   string `json:"address"`
	Password1 string `json:"password1"`
	Password2 string `json:"password2"`
}

// RegisterHandler godoc
// @Summary Register a new user
// @Description Register a new user with the provided information
// @Tags auth
// @Accept json
// @Produce json
// @Param request body RegisterRequest true "User registration details"
// @Success 201 {object} models.RegisterResponse "User registered successfully"
// @Failure 400 {object} models.ErrorResponse "Invalid request or passwords don't match"
// @Failure 409 {object} models.ErrorResponse "Email already exists"
// @Router /api/auth/register [post]
func (h *Handler) RegisterHandler(c *gin.Context) {
	registerRequest := &RegisterRequest{}
	if err := c.BindJSON(registerRequest); err != nil {
		h.logger.WithFields(logrus.Fields{
			"path": "handlers/auth.go",
		}).Error("bad bind json", err)
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// cache
	if _, exists := h.cache.Get(registerRequest.Email); exists {
		h.logger.WithFields(logrus.Fields{
			"path": "handlers/auth.go",
		}).Error("email already exists in cache")
		c.JSON(http.StatusConflict, gin.H{"error": "email already exists"})
		return
	} else if exists := h.psql.IsRegistered(registerRequest.Email); exists {
		h.logger.WithFields(logrus.Fields{
			"path": "handlers/auth.go",
		}).Error("email already exists in db")
		c.JSON(http.StatusConflict, gin.H{"error": "email already exists"})
		return
	}

	if registerRequest.Password1 != registerRequest.Password2 {
		h.logger.WithFields(logrus.Fields{
			"path": "handlers/auth.go",
		}).Error("passwords don't match")
		c.JSON(http.StatusBadRequest, gin.H{"error": "passwords do not match"})
		return
	}
	hash, err := utils.HashPassword(registerRequest.Password1)
	if err != nil {
		h.logger.WithFields(logrus.Fields{
			"path": "handlers/auth.go",
		}).Error("hashing error", err)
		c.JSON(http.StatusBadRequest, gin.H{"error": "hashing error"})
		return
	}
	user := &models.User{
		ID:       uuid.New().String(),
		Name:     registerRequest.Name,
		LastName: registerRequest.LastName,
		Country:  registerRequest.Country,
		Phone:    registerRequest.Phone,
		Email:    registerRequest.Email,
		Address:  registerRequest.Address,
		Password: hash,
		IsAdmin:  false,
	}
	h.psql.CreateUser(user)
	h.cache.Set(user.Email, user, cache.DefaultExpiration)
	h.logger.Info(logrus.Fields{"message": "user registered", "user": user})
	c.JSON(http.StatusCreated, gin.H{"message": "user registered"})
}

// AuthMiddleware godoc
// @Summary Authentication middleware
// @Description Middleware to authenticate JWT tokens
// @Tags auth
// @Security ApiKeyAuth
// @Failure 401 {object} map[string]interface{} "error"
// @Failure 500 {object} map[string]interface{} "error"
func (h Handler) AuthMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		// Extract token from header
		authHeader := c.GetHeader("Authorization")
		if authHeader == "" {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "Authorization header is required"})
			return
		}

		tokenParts := strings.Split(authHeader, "Bearer ")
		if len(tokenParts) != 2 {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "Invalid authorization format"})
			return
		}
		tokenString := tokenParts[1]

		// Verify token signature
		token, err := h.jwt.Authenticate(tokenString)

		if err != nil || !token.Valid {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "Invalid token"})
			return
		}

		// Check revoked tokens in Redis
		claims, ok := token.Claims.(jwt.MapClaims)
		if !ok {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "Invalid token claims"})
			return
		}

		userID, ok := claims["user_id"].(string)
		if !ok {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "Invalid user ID in token"})
			return
		}

		// Check blacklist
		exists, err := h.redis.GetJWT(userID)
		if err != nil {
			c.AbortWithStatusJSON(http.StatusInternalServerError, gin.H{"error": "Internal server error"})
			return
		}
		if exists.Token == "" {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "Token revoked"})
			return
		}

		// Save user_id in Gin context
		c.Set("user_id", userID)

		// Pass control to the next handler
		c.Next()
	}
}
