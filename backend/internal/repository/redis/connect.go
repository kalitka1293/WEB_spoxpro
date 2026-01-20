package redis

import (
	"context"
	"fmt"
	"time"

	"github.com/redis/go-redis/v9"
	"github.com/sirupsen/logrus"
)

type RedisConfig struct {
	Address  string `toml:"address"`
	Password string `toml:"password"`
	Database int    `toml:"database"`
}

func (r *RedisConfig) RedisConnect() (*redis.Client, error) {
	// redis connection
	redis := redis.NewClient(&redis.Options{
		Addr:     r.Address,
		Password: r.Password,
		DB:       r.Database,
	})
	if err := checkRedisConnection(redis); err != nil {
		return nil, err
	}

	return redis, nil
}

var ctx = context.Background()

func checkRedisConnection(client *redis.Client) error {
	ctx, cancel := context.WithTimeout(ctx, 3*time.Second)
	defer cancel()

	pong, err := client.Ping(ctx).Result()
	if err != nil {
		return fmt.Errorf("connection failed: %v", err)
	}

	fmt.Printf("Redis response: %s\n", pong)
	return nil
}

type Redis struct {
	redis *redis.Client
	logger *logrus.Logger
	ctx context.Context
}

func NewRedis(r *redis.Client, logger *logrus.Logger, ctx context.Context) *Redis {
	return &Redis{redis: r, logger: logger, ctx: ctx}
}