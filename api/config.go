package main

type Config struct {
	Port        int    `yaml:"port" validate:"required"`
	URL         string `yaml:"url" validate:"required"`
	DPSecret    string `yaml:"dp_secret" validate:"required"`
	DatabaseURL string `yaml:"database_url" validate:"required"`
}
