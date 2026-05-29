# SAO-Server (ForgeStack) ⚔️

[![Linux Compatibility](https://img.shields.io/badge/OS-Arch%20Linux%20Based-blue?style=flat-for-the-badge&logo=arch-linux)](https://archlinux.org)
[![Python Version](https://img.shields.io/badge/Python-3.10%2B-yellow?style=flat-for-the-badge&logo=python)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/UI-PyQt6-green?style=flat-for-the-badge&logo=qt)](https://www.qt.io/)
[![License](https://img.shields.io/badge/License-MIT-lightgrey?style=flat-for-the-badge)](https://opensource.org/licenses/MIT)

**SAO-Server** es un panel de control y administrador de servicios locales diseñado para entornos **Arch Linux y distribuciones derivadas** (como CachyOS, EndeavourOS, Manjaro, etc.). Desarrollado en Python utilizando PyQt6, unifica la gestión del stack LAMP (Apache, MySQL/MariaDB y PHP) bajo una interfaz gráfica moderna e inmersiva, inspirada en la estética HUD de *Sword Art Online*.

⚠️ **Nota:** Este es un proyecto de desarrollo **no comercial**, creado con fines educativos y de mejora del flujo de trabajo personal.

## ✨ Características Principales

* **Control Centralizado:** Gestión intuitiva de servicios `systemd` para Apache, MySQL y PHP.
* **Monitoreo Visual:** Interfaz con diseño inspirado en SAO que permite verificar el estado de tus servicios al instante.
* **Optimizado para Arch:** Integración nativa con los gestores de paquetes y servicios de Arch-based distros.
* **Uso Personal:** Diseñado para simplificar la vida del desarrollador web que trabaja localmente.

## 🚀 Instalación y Uso (Cualquier distro basada en Arch)

Sigue estos pasos desde tu terminal para poner en marcha el servidor en tu sistema:

### 1. Preparar el entorno
Asegúrate de tener instalados los componentes necesarios del stack LAMP:
```bash
sudo pacman -S apache mariadb php php-apache
