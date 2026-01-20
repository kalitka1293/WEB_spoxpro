package psql

import (
	"context"
	"fmt"

	"github.com/YoungGoofy/shopping/backend/internal/models"
	"github.com/sirupsen/logrus"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

type PSQLConfig struct {
	Host     string `toml:"host"`
	Port     int    `toml:"port"`
	User     string `toml:"user"`
	Password string `toml:"password"`
	Database string `toml:"database"`
}

func (p *PSQLConfig) PSQLConnect() (*gorm.DB, error) {
	dns := fmt.Sprintf("host=%v user=%v password=%v dbname=%v port=%v",
		p.Host,
		p.User,
		p.Password,
		p.Database,
		p.Port)
	psql, err := gorm.Open(postgres.Open(dns), &gorm.Config{})
	if err != nil {
		return nil, err
	}
	return psql, nil
}

type PSQL struct {
	psql   *gorm.DB
	logger *logrus.Logger
	ctx    context.Context
}

func NewPSQL(db *gorm.DB, logger *logrus.Logger, ctx context.Context) *PSQL {
	db.AutoMigrate(&models.User{})
	return &PSQL{psql: db, logger: logger, ctx: ctx}
}
