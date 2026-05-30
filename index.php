<?php
/**
 * SAO ForgeStack Explorer - Improved Edition
 * Autonomous recursive navigation with project detection + launch capabilities
 * Version: 2.0 (Neon Glassmorphism + Smart Routing)
 */

// 1. CONFIGURACIÓN Y SEGURIDAD
$baseDir = realpath(__DIR__);
$queryDir = isset($_GET['dir']) ? $_GET['dir'] : '';

// Limpiar ruta: eliminar intentos de directory traversal
$cleanPath = preg_replace('/\.\.|\\\\/', '', $queryDir);
$currentFullPath = realpath($baseDir . DIRECTORY_SEPARATOR . $cleanPath);

// Validar que no salimos del directorio raíz permitido
if (!$currentFullPath || strpos($currentFullPath, $baseDir) !== 0) {
    $currentFullPath = $baseDir;
    $cleanPath = '';
}

// 2. OBTENER ELEMENTOS DEL DIRECTORIO ACTUAL
$ignored = ['.', '..', '.git', 'node_modules', 'vendor', '.env', '.idea', '.DS_Store', 'thumbs.db'];
$items = @scandir($currentFullPath);
if ($items === false) {
    $items = [];
}
$items = array_diff($items, $ignored);

// 3. CLASIFICAR CARPETAS (y contar elementos internos)
$folders = [];
foreach ($items as $item) {
    $fullPath = $currentFullPath . DIRECTORY_SEPARATOR . $item;
    if (is_dir($fullPath)) {
        // Detectar si es proyecto ejecutable
        $isProject = false;
        $identifiers = ['index.php', 'index.html', 'index.htm', 'composer.json', 'package.json'];
        foreach ($identifiers as $id) {
            if (file_exists($fullPath . DIRECTORY_SEPARATOR . $id)) {
                $isProject = true;
                break;
            }
        }
        
        // Contar elementos internos (útil para el usuario)
        $subItems = @scandir($fullPath);
        $subCount = $subItems ? count(array_diff($subItems, $ignored)) : 0;
        
        $folders[] = [
            'name'     => $item,
            'relPath'  => trim($cleanPath . '/' . $item, '/'),
            'type'     => $isProject ? 'project' : 'container',
            'subCount' => $subCount
        ];
    }
}

// Orden alfabético
usort($folders, function($a, $b) {
    return strcasecmp($a['name'], $b['name']);
});

// 4. BREADCRUMBS
$breadcrumbs = array_filter(explode('/', $cleanPath));

// 5. URL BASE PARA LANZAR PROYECTOS (detecta automáticamente si estamos en subcarpeta)
$scriptName = $_SERVER['SCRIPT_NAME'] ?? 'index.php';
$baseWebPath = rtrim(dirname($scriptName), '/');
// Si estamos en la raíz, $baseWebPath será '', entonces concatenamos sin doble slash
if ($baseWebPath === '') {
    $baseWebPath = '';
} else {
    $baseWebPath = $baseWebPath . '/';
}
?>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes">
    <title>SAO ForgeStack | <?php echo $cleanPath ? '/' . htmlspecialchars($cleanPath) : 'ROOT'; ?></title>
    <style>
        /* ===== SAO GLASSMORPHISM + NEON THEME ===== */
        :root {
            --neon-cyan: #00ffcc;
            --neon-pink: #ff00aa;
            --bg-color: #05070a;
            --glass-bg: rgba(0, 255, 204, 0.05);
            --card-border: rgba(0, 255, 204, 0.3);
        }
        * {
            box-sizing: border-box;
        }
        body {
            background: var(--bg-color);
            color: #cfcfcf;
            font-family: 'Courier New', 'Fira Code', monospace;
            margin: 0;
            padding: 0;
            overflow-x: hidden;
        }
        .crt-overlay {
            position: fixed;
            inset: 0;
            background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%),
                        linear-gradient(90deg, rgba(255, 0, 0, 0.06), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.06));
            background-size: 100% 4px, 3px 100%;
            pointer-events: none;
            z-index: 9999;
        }
        .main-interface {
            padding: 30px 40px;
            opacity: 0;
            animation: fadeIn 0.6s forwards 0.4s;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(15px); }
            to { opacity: 1; transform: translateY(0); }
        }
        header.status-bar {
            border-bottom: 2px solid var(--neon-cyan);
            padding-bottom: 12px;
            margin-bottom: 30px;
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            flex-wrap: wrap;
            gap: 15px;
        }
        .breadcrumb {
            font-size: 14px;
            word-break: break-all;
        }
        .breadcrumb a {
            color: var(--neon-cyan);
            text-decoration: none;
            text-transform: uppercase;
            transition: text-shadow 0.2s;
        }
        .breadcrumb a:hover {
            text-shadow: 0 0 6px var(--neon-cyan);
        }
        .breadcrumb span {
            margin: 0 8px;
            color: #555;
        }
        .system-tag {
            font-size: 13px;
            background: rgba(0,255,204,0.1);
            padding: 6px 12px;
            border-radius: 20px;
            letter-spacing: 1px;
        }
        .search-bar {
            margin-bottom: 25px;
            display: flex;
            justify-content: flex-end;
        }
        #filterInput {
            background: rgba(0,0,0,0.6);
            border: 1px solid var(--neon-cyan);
            padding: 10px 18px;
            color: var(--neon-cyan);
            font-family: monospace;
            font-size: 14px;
            width: 280px;
            outline: none;
            transition: 0.2s;
        }
        #filterInput:focus {
            box-shadow: 0 0 12px var(--neon-cyan);
            border-color: var(--neon-cyan);
        }
        .project-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(290px, 1fr));
            gap: 22px;
        }
        .project-card {
            position: relative;
            border: 1px solid var(--card-border);
            padding: 20px;
            transition: 0.25s cubic-bezier(0.2, 0.9, 0.4, 1.1);
            background: var(--glass-bg);
            backdrop-filter: blur(2px);
            display: flex;
            flex-direction: column;
            text-decoration: none;
            color: #fff;
        }
        .project-card:hover {
            transform: translateY(-4px);
            border-color: var(--neon-cyan);
            box-shadow: 0 8px 25px rgba(0, 255, 204, 0.15);
            background: rgba(0, 255, 204, 0.02);
        }
        .project-card.type-project {
            border-left: 3px solid var(--neon-cyan);
        }
        .project-card.type-container {
            border-left: 3px solid #2c5368;
        }
        .card-header {
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 15px;
        }
        .icon {
            font-size: 38px;
            color: var(--neon-cyan);
        }
        .project-info {
            flex: 1;
        }
        .project-name {
            font-size: 1.1rem;
            font-weight: bold;
            margin: 0 0 6px 0;
            word-break: break-word;
            letter-spacing: 0.5px;
        }
        .badge {
            font-size: 9px;
            padding: 2px 8px;
            border: 1px solid var(--neon-cyan);
            color: var(--neon-cyan);
            text-transform: uppercase;
            background: rgba(0,0,0,0.5);
            display: inline-block;
        }
        .subinfo {
            font-size: 11px;
            color: #88aaff;
            margin-top: 5px;
        }
        .card-actions {
            margin-top: 18px;
            display: flex;
            gap: 12px;
            border-top: 1px dashed rgba(0,255,204,0.2);
            padding-top: 14px;
        }
        .btn-explore, .btn-launch {
            font-size: 12px;
            text-decoration: none;
            padding: 5px 12px;
            text-align: center;
            transition: 0.2s;
            font-family: monospace;
            font-weight: bold;
        }
        .btn-explore {
            background: transparent;
            border: 1px solid var(--neon-cyan);
            color: var(--neon-cyan);
        }
        .btn-launch {
            background: rgba(0,255,204,0.15);
            border: 1px solid #00ccaa;
            color: #ccffff;
        }
        .btn-explore:hover, .btn-launch:hover {
            background: var(--neon-cyan);
            color: #000;
            cursor: pointer;
        }
        .back-btn {
            grid-column: 1 / -1;
            text-align: center;
            border-style: dashed;
            background: rgba(0,255,204,0.02);
        }
        .back-btn .project-name {
            text-transform: uppercase;
            letter-spacing: 2px;
        }
        .empty-message {
            grid-column: 1/-1;
            text-align: center;
            padding: 60px 20px;
            border: 1px dotted #2c5368;
            opacity: 0.7;
            font-style: italic;
        }
        footer {
            margin-top: 50px;
            text-align: center;
            font-size: 11px;
            border-top: 1px solid #1a2a3a;
            padding-top: 20px;
            color: #667788;
        }
        /* LOADING SCREEN */
        #loading-screen {
            position: fixed;
            inset: 0;
            background: var(--bg-color);
            z-index: 10000;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            transition: opacity 0.5s ease;
        }
        .loading-text {
            font-size: 42px;
            letter-spacing: 12px;
            color: var(--neon-cyan);
            text-shadow: 0 0 12px var(--neon-cyan);
        }
        .progress-container {
            width: 320px;
            height: 2px;
            background: rgba(255,255,255,0.2);
            margin-top: 20px;
            overflow: hidden;
        }
        .loading-bar {
            width: 0%;
            height: 100%;
            background: var(--neon-cyan);
            box-shadow: 0 0 8px var(--neon-cyan);
        }
        @media (max-width: 700px) {
            .main-interface { padding: 20px; }
            .project-grid { gap: 15px; }
        }
    </style>
</head>
<body>
<div class="crt-overlay"></div>
<div id="loading-screen">
    <h1 class="loading-text">LINK START</h1>
    <div class="progress-container"><div class="loading-bar" id="bar"></div></div>
</div>

<div class="main-interface">
    <header class="status-bar">
        <div class="breadcrumb">
            <a href="index.php">◢ ROOT</a>
            <?php 
            $buildPath = '';
            foreach($breadcrumbs as $crumb): 
                $buildPath .= ($buildPath ? '/' : '') . $crumb;
            ?>
                <span>/</span><a href="index.php?dir=<?php echo urlencode($buildPath); ?>"><?php echo htmlspecialchars(strtoupper($crumb)); ?></a>
            <?php endforeach; ?>
        </div>
        <div class="system-tag">
            ⚡ FORGE // <span style="color:var(--neon-cyan)"><?php echo count($folders); ?> NODES</span>
        </div>
    </header>

    <div class="search-bar">
        <input type="text" id="filterInput" placeholder="[ FILTER NODES ]" autocomplete="off">
    </div>

    <main class="dashboard">
        <div class="project-grid" id="projectGrid">
            <?php if ($cleanPath !== ''): ?>
                <a href="index.php?dir=<?php echo urlencode(dirname($cleanPath) == '.' ? '' : dirname($cleanPath)); ?>" class="project-card back-btn">
                    <div class="project-name">⬆ RETURN TO UPPER LEVEL</div>
                </a>
            <?php endif; ?>

            <?php foreach($folders as $folder): 
                $isProject = ($folder['type'] === 'project');
                $exploreUrl = 'index.php?dir=' . urlencode($folder['relPath']);
                // Construir URL de lanzamiento absoluta (base web + ruta del proyecto)
                $launchUrl = $baseWebPath . $folder['relPath'] . '/';
                $badgeText = $isProject ? '⚔️ DEPLOYABLE' : '📂 DIRECTORY';
            ?>
                <div class="project-card type-<?php echo $folder['type']; ?>" data-name="<?php echo htmlspecialchars(strtolower($folder['name'])); ?>">
                    <div class="card-header">
                        <div class="icon"><?php echo $isProject ? '⚡' : '🗀'; ?></div>
                        <div class="project-info">
                            <div class="project-name"><?php echo htmlspecialchars($folder['name']); ?></div>
                            <span class="badge"><?php echo $badgeText; ?></span>
                            <div class="subinfo">📦 <?php echo $folder['subCount']; ?> elementos internos</div>
                        </div>
                    </div>
                    <div class="card-actions">
                        <a href="<?php echo $exploreUrl; ?>" class="btn-explore">🔍 EXPLORE</a>
                        <?php if ($isProject): ?>
                            <a href="<?php echo $launchUrl; ?>" target="_blank" class="btn-launch">▶ LAUNCH</a>
                        <?php else: ?>
                            <span style="flex:1; font-size:10px; color:#335; text-align:right;">[navigate]</span>
                        <?php endif; ?>
                    </div>
                </div>
            <?php endforeach; ?>

            <?php if (empty($folders)): ?>
                <div class="empty-message">
                    ⚠️ [ VACUUM DETECTED ] ⚠️<br>
                    No se encontraron subdirectorios en esta ubicación.
                </div>
            <?php endif; ?>
        </div>
    </main>
    <footer>
        SAO ForgeStack Explorer v2 &nbsp;|&nbsp; Secure recursive scan &nbsp;|&nbsp; <?php echo date('Y-m-d H:i:s'); ?>
    </footer>
</div>

<script>
    (function() {
        // LOADING ANIMATION (determinista + fluido)
        const bar = document.getElementById('bar');
        const loadingScreen = document.getElementById('loading-screen');
        let width = 0;
        const interval = setInterval(() => {
            if (width >= 100) {
                clearInterval(interval);
                if (loadingScreen) {
                    loadingScreen.style.opacity = '0';
                    setTimeout(() => {
                        if (loadingScreen.parentNode) loadingScreen.remove();
                    }, 500);
                }
                return;
            }
            width += Math.random() * 8 + 2;
            if (width > 100) width = 100;
            if (bar) bar.style.width = width + '%';
        }, 35);

        // FILTRO EN TIEMPO REAL (por nombre de carpeta)
        const filterInput = document.getElementById('filterInput');
        const cards = document.querySelectorAll('.project-card');
        const backButton = document.querySelector('.back-btn'); // para no filtrar el back

        function filterNodes() {
            const term = filterInput.value.trim().toLowerCase();
            cards.forEach(card => {
                // Si es el botón "back", siempre visible
                if (card.classList.contains('back-btn')) {
                    card.style.display = '';
                    return;
                }
                const nameAttr = card.getAttribute('data-name');
                if (nameAttr && nameAttr.includes(term)) {
                    card.style.display = '';
                } else {
                    card.style.display = 'none';
                }
            });
        }
        if (filterInput) {
            filterInput.addEventListener('input', filterNodes);
        }
    })();
</script>
</body>
</html>