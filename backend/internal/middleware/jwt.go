package middleware

import (
	"fmt"
	"os"
	"time"

	"github.com/BurntSushi/toml"
	"github.com/YoungGoofy/shopping/backend/internal/models"
	"github.com/golang-jwt/jwt/v5"
	"github.com/sirupsen/logrus"
)

type Config struct {
	JWT struct {
		SecretKey string `toml:"secret_key"`
	} `toml:"jwt"`
}

type JWTMiddleware struct {
	secretKey string
}

func NewJWTMiddleware(logger *logrus.Logger) *JWTMiddleware {
	var config Config
	data, err := os.ReadFile("config.toml")
	if err != nil {
		logger.WithFields(logrus.Fields{
			"file": "connect.go",
		}).Fatal(err)
		return nil
	}
	_, err = toml.Decode(string(data), &config)
	if err != nil {
		logger.WithFields(logrus.Fields{
			"file": "connect.go",
		}).Fatal(err)
		return nil
	}
	return &JWTMiddleware{
		secretKey: config.JWT.SecretKey,
	}
}

func (m *JWTMiddleware) Authenticate(tokenString string) (*jwt.Token, error) {
	token, err := jwt.Parse(tokenString, func(token *jwt.Token) (any, error) {
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
		}
		return []byte(m.secretKey), nil
	})
	if err != nil {
		return nil, err
	}
	return token, nil
}

func (m *JWTMiddleware) GenerateToken(user *models.User) (string, error) {
	u := models.User{
		ID: user.ID,
		Name: user.Name,
		LastName: user.LastName,
		Country: user.Country,
		Phone: user.Phone,
		Email: user.Email,
		Address: user.Address,
	}
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, jwt.MapClaims{
		"sub": u,
		"iss": "shopping",
		"aud": getRole(user.IsAdmin),
		"exp": time.Now().Add(time.Hour * 24).Unix(),
		"iat": time.Now().Unix(),
	})
	tokenString, err := token.SignedString([]byte(m.secretKey))
	if err != nil {
		return "", err
	}
	return tokenString, nil
}

func getRole(isAdmin bool) string {
	if isAdmin {
		return "admin"
	}
	return "user"
}


