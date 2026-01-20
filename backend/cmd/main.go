package main

import (
	"context"
	"io"
	"os"

	// Import the generated docs package
	_ "github.com/YoungGoofy/shopping/backend/docs"

	"github.com/YoungGoofy/shopping/backend/internal/routes"
	"github.com/sirupsen/logrus"
)

// @title Shopping API
// @version 1.0
// @description API for the shopping application
// @license.name Apache 2.0
// @license.url http://www.apache.org/licenses/LICENSE-2.0.html
// @BasePath /api
// @securityDefinitions.apikey ApiKeyAuth
// @in header
// @name Authorization
func main() {
	logFile, err := os.OpenFile("app.log", os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		panic(err)
	}
	defer logFile.Close()
	mw := io.MultiWriter(os.Stdout, logFile)
	logger := logrus.New()
	logger.SetOutput(mw)
	logger.Formatter = &logrus.JSONFormatter{}
	logger.Level = logrus.DebugLevel
	
	ctx := context.Background()
	router := routes.NewRouter(logger, ctx)
	router.Run()
}
