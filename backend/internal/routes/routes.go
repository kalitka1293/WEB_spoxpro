package routes

import (
	"context"
	"net/http"

	"github.com/YoungGoofy/shopping/backend/internal/handlers"
	"github.com/YoungGoofy/shopping/backend/internal/middleware"
	"github.com/YoungGoofy/shopping/backend/internal/repository"
	"github.com/YoungGoofy/shopping/backend/internal/repository/psql"
	"github.com/YoungGoofy/shopping/backend/internal/repository/redis"
	"github.com/gin-gonic/gin"
	"github.com/sirupsen/logrus"
	swaggerfiles "github.com/swaggo/files"
	ginSwagger "github.com/swaggo/gin-swagger"
)

type Router struct {
	logger *logrus.Logger
	psql   *psql.PSQL
	redis  *redis.Redis
	ctx    context.Context
}

func NewRouter(logger *logrus.Logger, ctx context.Context) *Router {
	dbs, err := repository.NewConnection(logger, ctx)
	if err != nil {
		logger.WithFields(logrus.Fields{
			"path": "routes/routes.go",
		}).Fatal("DBs not connected", err)
		return nil
	}
	return &Router{
		logger: logger,
		psql:   dbs.PSQL,
		redis:  dbs.Redis,
		ctx:    ctx,
	}
}

func (r *Router) Run() {
	router := gin.Default()
	r.setupRoutes(router)
	r.logger.Info("http://localhost:8080")
	r.logger.Info("Swagger documentation: http://localhost:8080/swagger/index.html")
	router.Run(":8080")
}

func (r *Router) setupRoutes(router *gin.Engine) {
	jwt := middleware.NewJWTMiddleware(r.logger)
	h := handlers.NewHandler(r.logger, jwt, r.psql, r.redis)
	
	// Serve Swagger documentation
	router.GET("/swagger/*any", ginSwagger.WrapHandler(swaggerfiles.Handler))
	
	// Health check endpoint
	router.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"status": "alive"})
	})
	
	api := router.Group("/api")
	{
		//not working now
		// api.Use(h.AuthMiddleware())
		auth := api.Group("/auth")
		{
			auth.POST("/login", h.LoginHandler)
			auth.POST("/register", h.RegisterHandler)
		}
		
	}
}
