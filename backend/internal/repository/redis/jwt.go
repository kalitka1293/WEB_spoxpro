package redis

import (
	"encoding/json"
	"fmt"
	"time"

	"github.com/sirupsen/logrus"
)

type jwtData struct {
	Uuid        string `json:"uuid"`
	Token       string `json:"token"`
	CreatedTime int64  `json:"created_time"`
}

func (r *Redis) AddJWT(uuid string, token string) error {
	key := fmt.Sprintf("jwt:%v", uuid)
	data := jwtData{
		Uuid:        uuid,
		Token:       token,
		CreatedTime: time.Now().Unix(),
	}
	jsonData, err := json.Marshal(data)
	if err != nil {
		r.logger.WithFields(logrus.Fields{
            "path": "redis/jwt.go",
        }).Error("Failed to marshal JWT data:", err)
        return fmt.Errorf("failed to marshal JWT data: %w", err)
	}
	if err := r.redis.Set(r.ctx, key, jsonData, 24 * time.Hour).Err(); err != nil {
		r.logger.WithFields(logrus.Fields{
			"path": "redis/jwt.go",
		}).Errorf("Failed to save token: %v", err)
		return fmt.Errorf("failed to save token: %w", err)
	}
	return nil
}

func (r *Redis) GetJWT(uuid string) (*jwtData, error) {
	key := fmt.Sprintf("jwt:%s", uuid)
    
    data, err := r.redis.Get(r.ctx, key).Bytes()
    if err != nil {
        return nil, fmt.Errorf("token not found: %w", err)
    }
    
    var jwtData jwtData
    if err := json.Unmarshal(data, &jwtData); err != nil {
        return nil, fmt.Errorf("failed to unmarshal JWT data: %w", err)
    }
    
    return &jwtData, nil
}