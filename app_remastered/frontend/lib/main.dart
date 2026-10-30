import 'dart:async';

import 'package:flutter/material.dart';

import 'services/api_service.dart';

void main() {
  runApp(const QueensApp());
}

class QueensApp extends StatelessWidget {
  const QueensApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Queens',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF38BDF8),
          brightness: Brightness.dark,
        ),
        scaffoldBackgroundColor: const Color(0xFF0F172A),
        appBarTheme: const AppBarTheme(
          backgroundColor: Color(0xFF0F172A),
          foregroundColor: Color(0xFFF8FAFC),
          centerTitle: false,
        ),
        filledButtonTheme: FilledButtonThemeData(
          style: FilledButton.styleFrom(
            minimumSize: const Size(0, 48),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(14),
            ),
          ),
        ),
      ),
      home: const GameScreen(),
    );
  }
}

class GameScreen extends StatefulWidget {
  const GameScreen({super.key});

  @override
  State<GameScreen> createState() => _GameScreenState();
}

class _GameScreenState extends State<GameScreen> {
  static const _regionColors = <Color>[
    Color(0xFFA7F3D0),
    Color(0xFFFDE68A),
    Color(0xFFBAE6FD),
    Color(0xFFDDD6FE),
    Color(0xFFFBCFE8),
    Color(0xFFFED7AA),
    Color(0xFFC7D2FE),
    Color(0xFFE2E8F0),
    Color(0xFFD9F99D),
    Color(0xFFFCA5A5),
    Color(0xFF99F6E4),
    Color(0xFFF5D0FE),
  ];

  final ApiService _api = ApiService();
  Map<String, dynamic>? _game;
  int _size = 8;
  int _elapsedSeconds = 0;
  bool _loading = false;
  bool _crossMode = false;
  String? _loadError;
  Timer? _clock;

  @override
  void initState() {
    super.initState();
    _clock = Timer.periodic(const Duration(seconds: 1), (_) {
      if (mounted && _game?['timer_running'] == true) {
        setState(() => _elapsedSeconds++);
      }
    });
    _newGame();
  }

  @override
  void dispose() {
    _clock?.cancel();
    _api.close();
    super.dispose();
  }

  Future<void> _newGame() async {
    await _perform(() async {
      final game = await _api.createGame(_size, _game?['auto_cross'] ?? true);
      _applyGame(game);
      _crossMode = false;
    });
  }

  void _applyGame(Map<String, dynamic> game) {
    if (!mounted) return;
    setState(() {
      _game = game;
      _size = game['size'] as int;
      _elapsedSeconds = game['elapsed_seconds'] as int;
      _loadError = null;
    });
  }

  Future<void> _perform(Future<void> Function() action) async {
    if (_loading) return;
    setState(() => _loading = true);
    try {
      await action();
    } on ApiException catch (error) {
      if (mounted) {
        setState(() => _loadError = error.message);
        ScaffoldMessenger.of(context)
          ..hideCurrentSnackBar()
          ..showSnackBar(SnackBar(content: Text(error.message)));
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _tapCell(int row, int col) async {
    final game = _game;
    if (game == null || game['is_won'] == true) return;
    await _perform(() async {
      final updated = await _api.updateCell(
        game['game_id'] as String,
        row,
        col,
        _crossMode ? 'cross' : 'queen',
      );
      _applyGame(updated);
    });
  }

  Future<void> _undo() async {
    final game = _game;
    if (game == null) return;
    await _perform(() async {
      _applyGame(await _api.undo(game['game_id'] as String));
    });
  }

  Future<void> _reset() async {
    final game = _game;
    if (game == null) return;
    await _perform(() async {
      _applyGame(await _api.reset(game['game_id'] as String));
    });
  }

  Future<void> _hint() async {
    final game = _game;
    if (game == null) return;
    await _perform(() async {
      final response = await _api.hint(game['game_id'] as String);
      _applyGame(response['game'] as Map<String, dynamic>);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(response['message'] as String)),
        );
      }
    });
  }

  Future<void> _setAutoCross(bool enabled) async {
    final game = _game;
    if (game == null) return;
    await _perform(() async {
      _applyGame(
        await _api.setAutoCross(game['game_id'] as String, enabled),
      );
    });
  }

  String _formatTime(int seconds) {
    final minutes = (seconds ~/ 60).toString().padLeft(2, '0');
    final remaining = (seconds % 60).toString().padLeft(2, '0');
    return '$minutes:$remaining';
  }

  Color _regionColor(int region) =>
      _regionColors[region % _regionColors.length];

  Set<String> _errorCellKeys() {
    final validation = _game?['validation'] as Map<String, dynamic>?;
    final cells = validation?['error_cells'] as List<dynamic>? ?? const [];
    return cells.map((cell) => '${cell[0]},${cell[1]}').toSet();
  }

  Future<void> _showRecords() async {
    final size = _size;
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: const Color(0xFF1E293B),
      builder: (context) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 12, 20, 28),
          child: FutureBuilder<List<dynamic>>(
            future: _api.getRecords(size),
            builder: (context, snapshot) {
              return Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Récords · ${size}×$size',
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  const SizedBox(height: 14),
                  if (snapshot.connectionState == ConnectionState.waiting)
                    const Center(
                      child: Padding(
                        padding: EdgeInsets.all(24),
                        child: CircularProgressIndicator(),
                      ),
                    )
                  else if (snapshot.hasError)
                    Text('No se pudieron cargar los récords: ${snapshot.error}')
                  else if (snapshot.data!.isEmpty)
                    const Padding(
                      padding: EdgeInsets.symmetric(vertical: 20),
                      child: Text('Aún no hay partidas registradas.'),
                    )
                  else
                    ...snapshot.data!.asMap().entries.map((entry) {
                      final record = entry.value as Map<String, dynamic>;
                      return ListTile(
                        contentPadding: EdgeInsets.zero,
                        leading: CircleAvatar(
                          backgroundColor: const Color(0xFF334155),
                          child: Text('${entry.key + 1}'),
                        ),
                        title: Text(record['time_formatted'] as String),
                        subtitle: Text(
                          '${record['moves']} movimientos · ${record['date']}',
                        ),
                      );
                    }),
                ],
              );
            },
          ),
        ),
      ),
    );
  }

  Future<void> _showRules() async {
    await showModalBottomSheet<void>(
      context: context,
      backgroundColor: const Color(0xFF1E293B),
      builder: (context) => SafeArea(
        child: FutureBuilder<Map<String, dynamic>>(
          future: _api.getRules(),
          builder: (context, snapshot) {
            final rules = snapshot.data;
            return Padding(
              padding: const EdgeInsets.fromLTRB(24, 18, 24, 30),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Reglas del juego',
                      style: Theme.of(context).textTheme.titleLarge),
                  const SizedBox(height: 12),
                  if (snapshot.connectionState == ConnectionState.waiting)
                    const Center(child: CircularProgressIndicator())
                  else if (snapshot.hasError)
                    Text('No se pudieron cargar las reglas: ${snapshot.error}')
                  else ...[
                    Text(rules!['objective'] as String),
                    const SizedBox(height: 10),
                    ...(rules['constraints'] as List<dynamic>).map(
                      (rule) => Padding(
                        padding: const EdgeInsets.only(bottom: 6),
                        child: Text('• $rule'),
                      ),
                    ),
                    const SizedBox(height: 8),
                    const Text(
                      'Toca para colocar una reina. Cambia a modo Cruz para '
                      'marcar casillas. Las pistas colocan una reina de una '
                      'solución válida.',
                    ),
                  ],
                ],
              ),
            );
          },
        ),
      ),
    );
  }

  Widget _buildBoard(Map<String, dynamic> game) {
    final size = game['size'] as int;
    final regions = game['regions'] as List<dynamic>;
    final board = game['board'] as List<dynamic>;
    final errorKeys = _errorCellKeys();

    return LayoutBuilder(
      builder: (context, constraints) {
        final dimension = constraints.maxWidth;
        return Center(
          child: SizedBox.square(
            dimension: dimension,
            child: GridView.builder(
              physics: const NeverScrollableScrollPhysics(),
              padding: EdgeInsets.zero,
              itemCount: size * size,
              gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: size,
              ),
              itemBuilder: (context, index) {
                final row = index ~/ size;
                final col = index % size;
                final region = regions[row][col] as int;
                final state = board[row][col] as int;
                final regionRow = regions[row] as List<dynamic>;
                final bool top = row == 0 || regions[row - 1][col] != region;
                final bool bottom =
                    row == size - 1 || regions[row + 1][col] != region;
                final bool left = col == 0 || regionRow[col - 1] != region;
                final bool right =
                    col == size - 1 || regionRow[col + 1] != region;
                final isError = errorKeys.contains('$row,$col');
                final borderColor =
                    const Color(0xFF0F172A).withOpacity(0.78);
                return Semantics(
                  button: true,
                  label: 'Fila ${row + 1}, columna ${col + 1}',
                  child: InkWell(
                    onTap: _loading ? null : () => _tapCell(row, col),
                    child: Container(
                      decoration: BoxDecoration(
                        color: isError ? const Color(0xFFFCA5A5) : _regionColor(region),
                        border: Border(
                          top: BorderSide(
                            color: borderColor,
                            width: top ? 1.2 : 0.5,
                          ),
                          bottom: BorderSide(
                            color: borderColor,
                            width: bottom ? 1.2 : 0.5,
                          ),
                          left: BorderSide(
                            color: borderColor,
                            width: left ? 1.2 : 0.5,
                          ),
                          right: BorderSide(
                            color: borderColor,
                            width: right ? 1.2 : 0.5,
                          ),
                        ),
                      ),
                      alignment: Alignment.center,
                      child: state == 1
                          ? Icon(
                              Icons.workspace_premium_rounded,
                              color: isError
                                  ? const Color(0xFFB91C1C)
                                  : const Color(0xFFB45309),
                              size: dimension / size * 0.68,
                            )
                          : state == 2
                              ? Icon(
                                  Icons.close_rounded,
                                  color: const Color(0xFF334155),
                                  size: dimension / size * 0.48,
                                )
                              : null,
                    ),
                  ),
                );
              },
            ),
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final game = _game;
    return Scaffold(
      appBar: AppBar(
        title: const Row(
          children: [
            Icon(Icons.workspace_premium_rounded, color: Color(0xFFFBBF24)),
            SizedBox(width: 8),
            Text('QUEENS', style: TextStyle(fontWeight: FontWeight.w800)),
          ],
        ),
        actions: [
          IconButton(
            tooltip: 'Récords',
            onPressed: _showRecords,
            icon: const Icon(Icons.emoji_events_outlined),
          ),
          IconButton(
            tooltip: 'Reglas',
            onPressed: _showRules,
            icon: const Icon(Icons.help_outline_rounded),
          ),
        ],
      ),
      body: game == null
          ? Center(
              child: Padding(
                padding: const EdgeInsets.all(28),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    if (_loading)
                      const CircularProgressIndicator()
                    else
                      const Icon(
                        Icons.cloud_off_rounded,
                        color: Color(0xFFF87171),
                        size: 40,
                      ),
                    const SizedBox(height: 16),
                    Text(
                      _loadError ?? 'Conectando con el servidor…',
                      textAlign: TextAlign.center,
                    ),
                    if (!_loading) ...[
                      const SizedBox(height: 12),
                      FilledButton.icon(
                        onPressed: _newGame,
                        icon: const Icon(Icons.refresh_rounded),
                        label: const Text('Reintentar'),
                      ),
                    ],
                  ],
                ),
              ),
            )
          : SafeArea(
              top: false,
              child: Stack(
                children: [
                  ListView(
                    padding: const EdgeInsets.fromLTRB(16, 4, 16, 28),
                    children: [
                      Row(
                        children: [
                          Expanded(
                            child: Text(
                              'Un reto de lógica',
                              style: Theme.of(context)
                                  .textTheme
                                  .titleMedium
                                  ?.copyWith(color: const Color(0xFF94A3B8)),
                            ),
                          ),
                          DropdownButton<int>(
                            value: _size,
                            dropdownColor: const Color(0xFF1E293B),
                            underline: const SizedBox.shrink(),
                            items: List.generate(
                              9,
                              (index) => DropdownMenuItem(
                                value: index + 4,
                                child: Text('${index + 4}×${index + 4}'),
                              ),
                            ),
                            onChanged: _loading
                                ? null
                                : (value) {
                                    if (value != null) {
                                      setState(() => _size = value);
                                      _newGame();
                                    }
                                  },
                          ),
                          IconButton(
                            tooltip: 'Nuevo mapa',
                            onPressed: _loading ? null : _newGame,
                            icon: const Icon(Icons.casino_outlined),
                          ),
                        ],
                      ),
                      const SizedBox(height: 10),
                      Row(
                        children: [
                          Expanded(
                            child: _StatCard(
                              icon: Icons.workspace_premium_rounded,
                              label: 'REINAS',
                              value: '${game['queen_count']} / $_size',
                              color: const Color(0xFFFBBF24),
                            ),
                          ),
                          const SizedBox(width: 10),
                          Expanded(
                            child: _StatCard(
                              icon: Icons.timer_outlined,
                              label: 'TIEMPO',
                              value: _formatTime(_elapsedSeconds),
                              color: const Color(0xFF38BDF8),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 16),
                      Card(
                        child: Padding(
                          padding: const EdgeInsets.all(12),
                          child: Center(
                            child: ConstrainedBox(
                              constraints: const BoxConstraints(maxWidth: 560),
                              child: AspectRatio(
                                aspectRatio: 1,
                                child: _buildBoard(game),
                              ),
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(height: 10),
                      Row(
                        children: [
                          const Expanded(
                            child: Text('Modo de juego',
                                style: TextStyle(
                                    color: Color(0xFFCBD5E1),
                                    fontWeight: FontWeight.w600)),
                          ),
                          Switch.adaptive(
                            value: game['auto_cross'] as bool,
                            onChanged: _loading ? null : _setAutoCross,
                          ),
                          const Text('Auto-cruces',
                              style: TextStyle(color: Color(0xFF94A3B8))),
                        ],
                      ),
                      const SizedBox(height: 4),
                      SegmentedButton<bool>(
                        segments: const [
                          ButtonSegment(
                            value: false,
                            icon: Icon(Icons.workspace_premium_outlined),
                            label: Text('Reina'),
                          ),
                          ButtonSegment(
                            value: true,
                            icon: Icon(Icons.close_rounded),
                            label: Text('Cruces'),
                          ),
                        ],
                        selected: {_crossMode},
                        onSelectionChanged: _loading
                            ? null
                            : (selection) =>
                                setState(() => _crossMode = selection.first),
                      ),
                      const SizedBox(height: 12),
                      Row(
                        children: [
                          Expanded(
                            child: OutlinedButton.icon(
                              onPressed: _loading ? null : _reset,
                              icon: const Icon(Icons.restart_alt_rounded),
                              label: const Text('Reiniciar'),
                            ),
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: OutlinedButton.icon(
                              onPressed: _loading ? null : _undo,
                              icon: const Icon(Icons.undo_rounded),
                              label: const Text('Deshacer'),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      FilledButton.icon(
                        onPressed: _loading || game['is_won'] == true
                            ? null
                            : _hint,
                        icon: const Icon(Icons.lightbulb_outline_rounded),
                        label: const Text('Dame una pista'),
                      ),
                      const SizedBox(height: 12),
                      if (game['is_won'] == true)
                        Card(
                          color: const Color(0xFF064E3B),
                          child: Padding(
                            padding: const EdgeInsets.all(16),
                            child: Column(
                              children: [
                                const Icon(Icons.celebration_rounded,
                                    color: Color(0xFF6EE7B7), size: 32),
                                const SizedBox(height: 8),
                                Text(
                                  game['last_message'] as String,
                                  textAlign: TextAlign.center,
                                  style: const TextStyle(
                                      fontWeight: FontWeight.w700),
                                ),
                                const SizedBox(height: 10),
                                TextButton(
                                  onPressed: _newGame,
                                  child: const Text('Siguiente partida'),
                                ),
                              ],
                            ),
                          ),
                        )
                      else
                        Text(
                          game['last_message'] as String,
                          textAlign: TextAlign.center,
                          style: const TextStyle(color: Color(0xFF94A3B8)),
                        ),
                      const SizedBox(height: 8),
                      const Text(
                        'Una reina por fila, columna y región. Las reinas no '
                        'pueden tocarse, tampoco en diagonal.',
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          color: Color(0xFF64748B),
                          fontSize: 12,
                        ),
                      ),
                    ],
                  ),
                  if (_loading)
                    const Positioned(
                      top: 0,
                      left: 0,
                      right: 0,
                      child: LinearProgressIndicator(minHeight: 2),
                    ),
                ],
              ),
            ),
    );
  }
}

class _StatCard extends StatelessWidget {
  const _StatCard({
    required this.icon,
    required this.label,
    required this.value,
    required this.color,
  });

  final IconData icon;
  final String label;
  final String value;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        child: Row(
          children: [
            Icon(icon, color: color),
            const SizedBox(width: 10),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  label,
                  style: const TextStyle(
                    color: Color(0xFF94A3B8),
                    fontSize: 10,
                    letterSpacing: 1,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const SizedBox(height: 2),
                Text(value,
                    style: const TextStyle(
                        fontSize: 17, fontWeight: FontWeight.w700)),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
