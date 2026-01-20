package psql

import (
	"fmt"

	"github.com/YoungGoofy/shopping/backend/internal/models"
)

func (p *PSQL) CreateCategory(category *models.Category) error {
	return createCategory(p, category)
}

func (p *PSQL) GetCategory(id uint) (models.Category, error) {
	return getCategory(p, id)
}

func (p *PSQL) GetCategories() ([]models.Category, error) {
	return getCategories(p)
}

func (p *PSQL) DeleteCategories(id uint) error {
	return deleteCategories(p, id)
}

func (p *PSQL) GetCategoryWithRelations(id uint) (*models.Category, error) {
	return getCategoryWithRelations(p, id)
}

func createCategory(p *PSQL, category *models.Category) error {
	res := p.psql.Create(&category)
	if res.Error != nil {
		return fmt.Errorf("new row didn't add in table 'category':\n%v", res.Error)
	}
	return nil
}

func getCategory(p *PSQL, id uint) (models.Category, error) {
	var category = models.Category{ID: id}
	result := p.psql.First(&category)
	if result.Error != nil {
		return models.Category{}, fmt.Errorf("category not found:\n%v", result.Error)
	}
	return category, nil
}

func getCategories(p *PSQL) ([]models.Category, error) {
	var category []models.Category
	result := p.psql.Find(&category)
	if result.Error != nil {
		return []models.Category{}, fmt.Errorf("category not found:\n%v", result.Error)
	}
	return category, nil
}

func deleteCategories(p *PSQL, id uint) error {
	// Сначала ищем дочерние категории
	var children []models.Category
	if err := p.psql.Where("parent_id = ?", id).Find(&children).Error; err != nil {
		return fmt.Errorf("failed to find child categories:\n%v", err)
	}

	// Рекурсивно удаляем дочерние категории
	for _, child := range children {
		if err := deleteCategories(p, child.ID); err != nil {
			return err
		}
	}

	// Удаляем текущую категорию
	result := p.psql.Delete(&models.Category{}, id)
	if result.Error != nil {
		return fmt.Errorf("failed to delete category with id %d:\n%v", id, result.Error)
	}

	return nil
}

func getCategoryWithRelations(p *PSQL, id uint) (*models.Category, error) {
	var category models.Category
	res := p.psql.Preload("Parent").Preload("Children").First(&category, id)
	if res.Error != nil {
		return nil, fmt.Errorf("failed to retrieve category with relations:\n%v", res.Error)
	}
	return &category, nil
}
