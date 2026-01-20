package handlers

import (
	"time"

	"github.com/YoungGoofy/shopping/backend/internal/middleware"
	"github.com/YoungGoofy/shopping/backend/internal/repository/psql"
	"github.com/YoungGoofy/shopping/backend/internal/repository/redis"
	"github.com/patrickmn/go-cache"
	"github.com/sirupsen/logrus"
)

type Handler struct {
	logger *logrus.Logger
	jwt   *middleware.JWTMiddleware
	cache *cache.Cache
	psql  *psql.PSQL
	redis *redis.Redis
}

func NewHandler(logger *logrus.Logger,jwt *middleware.JWTMiddleware, psql *psql.PSQL, redis *redis.Redis) *Handler {
	c := cache.New(12*time.Hour, 13*time.Hour)
	return &Handler{
		logger: logger,
		jwt:   jwt,
		cache: c,
		psql:  psql,
		redis: redis,
	}
}
