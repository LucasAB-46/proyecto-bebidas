// src/context/LocalContext.jsx
import React, { createContext, useState, useEffect, useContext } from 'react';
import api from '../api/client.jsx'; // <-- CORREGIDO

const LocalContext = createContext();

export const useLocal = () => useContext(LocalContext);

export const LocalProvider = ({ children }) => {
    const [locales, setLocales] = useState([]);
    const [selectedLocal, setSelectedLocal] = useState(null);
    const [loadingLocales, setLoadingLocales] = useState(true);

    useEffect(() => {
        const fetchLocales = async () => {
            try {
                const response = await api.get('/core/locales/');
                setLocales(response.data);
                if (response.data.length > 0) {
                    setSelectedLocal(response.data[0]);
                }
            } catch (error) {
                console.error("Error al cargar los locales:", error);
            } finally {
                setLoadingLocales(false);
            }
        };
        fetchLocales();
    }, []);

    const value = { locales, selectedLocal, setSelectedLocal, loadingLocales };

    return <LocalContext.Provider value={value}>{children}</LocalContext.Provider>;
};