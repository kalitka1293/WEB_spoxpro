package repository

import (
	"context"
	"os"

	"github.com/BurntSushi/toml"
	"github.com/YoungGoofy/shopping/backend/internal/repository/psql"
	r "github.com/YoungGoofy/shopping/backend/internal/repository/redis"
	"github.com/sirupsen/logrus"
)

type Config struct {
	Database struct {
		PSQL  psql.PSQLConfig `toml:"psql"`
		Redis r.RedisConfig   `toml:"redis"`
	} `toml:"database"`
	logger logrus.Logger
}

func newConfig(logger *logrus.Logger) *Config {
	var config Config
	data, err := os.ReadFile("config.toml")
	if err != nil {
		logger.WithFields(logrus.Fields{
			"path": "repository/connect.go",
		}).Fatal("Error reading config:", err)
		return nil
	}
	_, err = toml.Decode(string(data), &config)
	if err != nil {
		logger.WithFields(logrus.Fields{
			"file": "repository/connect.go",
		}).Fatal("Error decoding config:", err)
		return nil
	}
	
	return &config
}

type Databases struct {
	PSQL  *psql.PSQL
	Redis *r.Redis
}

func NewConnection(logger *logrus.Logger, ctx context.Context) (*Databases, error) {
	config := newConfig(logger)
	psqlConf, err := config.Database.PSQL.PSQLConnect()
	if err != nil {
		logger.WithFields(logrus.Fields{
			"path": "repository/connect.go",
		}).Fatal(err)
	} else {
		logger.Info("psql db opened")
	}

	redisConf, err := config.Database.Redis.RedisConnect()
	if err != nil {
		logger.WithFields(logrus.Fields{
			"path": "repository/connect.go",
		}).Fatal(err)
	} else {
		logger.Info("redis db opened")
	}
	
	psql := psql.NewPSQL(psqlConf, logger, ctx)
	redis := r.NewRedis(redisConf, logger, ctx)
	return &Databases{PSQL: psql, Redis: redis}, nil
}
