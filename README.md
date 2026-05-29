# SAO-Server (ForgeStack) ⚔️

[![Linux Compatibility](https://img.shields.io/badge/OS-Arch%20Linux%20%7C%20CachyOS-blue?style=flat-for-the-badge&logo=arch-linux)](https://archlinux.org)
[![Python Version](https://img.shields.io/badge/Python-3.10%2B-yellow?style=flat-for-the-badge&logo=python)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/UI-PyQt6-green?style=flat-for-the-badge&logo=qt)](https://www.qt.io/)

**SAO-Server** es un panel de control y administrador de servicios locales diseñado para entornos basados en **Arch Linux**. Desarrollado en Python utilizando PyQt6, unifica la gestión del stack web clásico (Apache, MySQL/MariaDB y PHP) bajo una interfaz gráfica moderna e inmersiva fuertemente inspirada en la estética HUD de *Sword Art Online*.

La herramienta busca automatizar el flujo de trabajo de desarrollo local, reemplazando los comandos repetitivos de la terminal por interacciones visuales rápidas y fluidas.

## ✨ Características Principales

* **Control Centralizado de Servicios:** Inicia, detiene y reinicia de forma independiente o global servicios esenciales como `httpd` (Apache), `mysqld` (MariaDB/MySQL) y configuraciones de PHP.
* **Monitoreo en Tiempo Real:** Indicadores visuales de estado que reflejan de inmediato si un servicio está activo, inactivo o reportando fallos en el sistema a través de `systemd`.
* **Diseño Inmersivo (SAO Style):** Interfaz limpia y estilizada con layouts modulares que capturan la esencia visual del anime, optimizando el espacio de trabajo.
* **Gestión de Dependencias:** Automatización básica en el backend para verificar que los servicios requeridos estén instalados y configurados correctamente en la distribución.

## 🛠️ Stack Tecnológico

* **Lenguaje:** [Python 3](https://www.python.org/)
* **Interfaz Gráfica:** [PyQt6](https://pypi.org/project/PyQt6/) (Bindings de Qt6)
* **Gestión del Sistema:** Integración nativa con `systemctl` y políticas de backend de GNU/Linux.
* **Entorno Soportado:** Apache HTTP Server, MySQL/MariaDB, PHP 8.x.

## 🚀 Instalación y Uso

### Requisitos Previos

Asegúrate de tener instalados los servicios web en tu sistema Arch/CachyOS:
```bash
sudo pacman -S apache mariadb php php-apache
