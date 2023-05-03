package main

import (
	"encoding/json"
	"net/http"

	"github.com/go-chi/chi/v5"
)

type AddressBook struct {
	Name   string
	UserID string
	Role   string
	IsHOD  bool
}

func loadApi(r *chi.Mux) {
	r.Post("/api/getAddressBook", func(w http.ResponseWriter, r *http.Request) {
		rows, err := pool.Query(ctx, "SELECT user_id, name, role_name, is_hod FROM users")

		if err != nil {
			w.WriteHeader(http.StatusInternalServerError)
			w.Write([]byte("Error while querying database."))
			return
		}

		var addressBook []AddressBook

		for rows.Next() {
			var userId string
			var name string
			var role string
			var isHod bool

			err := rows.Scan(&userId, &name, &role, &isHod)

			if err != nil {
				w.WriteHeader(http.StatusInternalServerError)
				w.Write([]byte("Error while querying database."))
				return
			}

			addressBook = append(addressBook, AddressBook{
				Name:   name,
				UserID: userId,
				Role:   role,
				IsHOD:  isHod,
			})
		}

		bytes, err := json.Marshal(addressBook)

		if err != nil {
			w.WriteHeader(http.StatusInternalServerError)
			w.Write([]byte("Error while sending JSON response."))
			return
		}

		w.Header().Set("Content-Type", "application/json")
		w.Write(bytes)
	})
}
