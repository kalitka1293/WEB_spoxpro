package psql

import (
	"fmt"

	"github.com/YoungGoofy/shopping/backend/internal/models"
)

func (p *PSQL) CreateUser(user *models.User) error {
	return createUser(p, user)
}

func (p *PSQL) GetUser(email string) (models.User, error) {
	return getUser(p, email)
}

func (p *PSQL) IsRegistered(email string) bool {
	if _, err := getUser(p, email); err == nil {
		return true
	}
	return false
}

func createUser(p *PSQL, user *models.User) error {
	res := p.psql.Create(&user)
	if res.Error != nil {
		return fmt.Errorf("new row didn't add in table 'user':\n%v", res.Error)
	}
	return nil
}

func getUser(p *PSQL, email string) (models.User, error) {
	var user models.User
	result := p.psql.First(&user, "email = ?", email)
	if result.Error != nil {
		return models.User{}, fmt.Errorf("user not found:\n%v", result.Error)
	}
	return user, nil
}
