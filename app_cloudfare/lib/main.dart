import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'services/api_service.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  SystemChrome.setPreferredOrientations([
    DeviceOrientation.portraitUp,
    DeviceOrientation.portraitDown,
  ]);
  runApp(const QueensApp());
}

// ─────────────────────────────────────────────────────────────────
// THEME & COLORS
// ─────────────────────────────────────────────────────────────────
const _bg       = Color(0xFF0F172A);
const _surface  = Color(0xFF1E293B);
const _accent   = Color(0xFF38BDF8);
const _textP    = Colors.white;
const _textS    = Color(0xFF94A3B8);
const _errC     = Color(0xFFFC8181);
const _winC     = Color(0xFF6EE7B7);

const List<Color> _palette = [
  Color(0xFFA7F3D0), Color(0xFFFDE68A), Color(0xFFBAE6FD),
  Color(0xFFDDD6FE), Color(0xFFFBCFE8), Color(0xFFFED7AA),
  Color(0xFFC7D2FE), Color(0xFFE2E8F0), Color(0xFFD9F99D),
  Color(0xFFFCA5A5), Color(0xFF99F6E4), Color(0xFFF5D0FE),
];
Color _rc(int r) => _palette[r % _palette.length];

// ─────────────────────────────────────────────────────────────────
// APP ROOT
// ─────────────────────────────────────────────────────────────────
class QueensApp extends StatelessWidget {
  const QueensApp({super.key});
  @override
  Widget build(BuildContext context) => MaterialApp(
    title: 'Queens',
    debugShowCheckedModeBanner: false,
    theme: ThemeData(
      colorScheme: ColorScheme.dark(primary: _accent, surface: _surface, error: _errC),
      scaffoldBackgroundColor: _bg,
      useMaterial3: true,
    ),
    home: const SizePickerScreen(),
  );
}

// ─────────────────────────────────────────────────────────────────
// SIZE PICKER
// ─────────────────────────────────────────────────────────────────
class SizePickerScreen extends StatelessWidget {
  const SizePickerScreen({super.key});
  @override
  Widget build(BuildContext context) => Scaffold(
    backgroundColor: _bg,
    body: SafeArea(
      child: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.workspace_premium_rounded, color: _accent, size: 72),
              const SizedBox(height: 16),
              const Text('Queens', style: TextStyle(color: _textP, fontSize: 40, fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              const Text(
                'Coloca una corona en cada fila, columna y región.\nNinguna puede tocar a otra.',
                textAlign: TextAlign.center,
                style: TextStyle(color: _textS, fontSize: 14),
              ),
              const SizedBox(height: 48),
              const Text('ELIGE TAMAÑO', style: TextStyle(color: _textS, fontSize: 12, letterSpacing: 1.5)),
              const SizedBox(height: 16),
              Wrap(
                spacing: 12, runSpacing: 12, alignment: WrapAlignment.center,
                children: List.generate(9, (i) => _SizeBtn(size: i + 4)),
              ),
              const SizedBox(height: 32),
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(color: _surface, borderRadius: BorderRadius.circular(12)),
                child: const Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Controles', style: TextStyle(color: _accent, fontWeight: FontWeight.bold)),
                    SizedBox(height: 8),
                    _HintRow(icon: Icons.touch_app, text: 'Toque → Cruz (marcar descartada)'),
                    _HintRow(icon: Icons.swipe, text: 'Arrastra → Cruces en todas las casillas'),
                    _HintRow(icon: Icons.ads_click, text: 'Doble toque → Corona (reina)'),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    ),
  );
}

class _HintRow extends StatelessWidget {
  final IconData icon;
  final String text;
  const _HintRow({required this.icon, required this.text});
  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 3),
    child: Row(
      children: [
        Icon(icon, color: _textS, size: 16),
        const SizedBox(width: 8),
        Expanded(child: Text(text, style: const TextStyle(color: _textS, fontSize: 13))),
      ],
    ),
  );
}

class _SizeBtn extends StatelessWidget {
  final int size;
  const _SizeBtn({required this.size});
  @override
  Widget build(BuildContext context) => ElevatedButton(
    style: ElevatedButton.styleFrom(
      backgroundColor: _surface, foregroundColor: _accent,
      minimumSize: const Size(76, 50),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      side: const BorderSide(color: Color(0xFF334155)),
    ),
    onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => GameScreen(boardSize: size))),
    child: Text('${size}×$size', style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600)),
  );
}

// ─────────────────────────────────────────────────────────────────
// GAME SCREEN
// ─────────────────────────────────────────────────────────────────
class GameScreen extends StatefulWidget {
  final int boardSize;
  const GameScreen({super.key, required this.boardSize});
  @override
  State<GameScreen> createState() => _GameScreenState();
}

class _GameScreenState extends State<GameScreen> {
  Map<String, dynamic>? _game;
  bool _loading = true;
  String?  _error;
  bool _autoCross = true;

  Timer? _ticker;
  int _elapsed = 0;

  // ── Touch interaction state ──────────────────────────────────
  /// Tracks if the current gesture started as a drag (pan)
  bool _isPan = false;
  /// Cells already crossed in the current drag gesture (avoid double-calls)
  final Set<String> _pannedCells = {};
  /// For double-tap detection: time and coords of last tap
  DateTime? _lastTapTime;
  int? _lastTapRow;
  int? _lastTapCol;
  static const _doubleTapWindow = Duration(milliseconds: 350);

  @override
  void initState() {
    super.initState();
    _newGame();
  }

  @override
  void dispose() {
    _ticker?.cancel();
    super.dispose();
  }

  // ─────────────────────────────────────────────────────────────
  // GAME ACTIONS
  // ─────────────────────────────────────────────────────────────
  Future<void> _newGame() async {
    _ticker?.cancel();
    setState(() { _loading = true; _error = null; _game = null; _elapsed = 0; });
    try {
      _apply(await ApiService.createGame(widget.boardSize));
    } catch (e) {
      setState(() { _error = e.toString(); _loading = false; });
    }
  }

  void _apply(Map<String, dynamic> g) {
    _ticker?.cancel();
    final won = g['is_won'] == true;
    _elapsed = (g['elapsed_seconds'] as num?)?.toInt() ?? 0;
    if (!won) {
      _ticker = Timer.periodic(const Duration(seconds: 1), (_) {
        if (mounted) setState(() => _elapsed++);
      });
    }
    setState(() { _game = g; _loading = false; _error = null; });
    if (won) _winDialog(g);
  }

  Future<void> _cell(int row, int col, String action) async {
    if (_game == null || _game!['is_won'] == true) return;
    try { _apply(await ApiService.updateCell(_game!['game_id'], row, col, action)); }
    catch (e) { _snack(e.toString()); }
  }

  Future<void> _undo()  async { try { _apply(await ApiService.undo(_game!['game_id']));  } catch (e) { _snack(e.toString()); } }
  Future<void> _reset() async { try { _apply(await ApiService.reset(_game!['game_id'])); } catch (e) { _snack(e.toString()); } }
  Future<void> _hint()  async { try { _apply(await ApiService.hint(_game!['game_id']));  } catch (e) { _snack(e.toString()); } }

  Future<void> _toggleAuto() async {
    if (_game == null) return;
    final next = !_autoCross;
    try {
      _apply(await ApiService.setAutoCross(_game!['game_id'], next));
      setState(() => _autoCross = next);
    } catch (e) { _snack(e.toString()); }
  }

  // ─────────────────────────────────────────────────────────────
  // TOUCH LOGIC
  // ─────────────────────────────────────────────────────────────

  /// Single-tap: toggle cross (0→cross, cross→empty, queen→cross)
  void _onSingleTap(int row, int col) {
    final board = _boardData;
    final cur = board[row][col];
    final action = cur == 2 ? 'empty' : 'cross';
    _cell(row, col, action);
  }

  /// Double-tap: place queen
  void _onDoubleTap(int row, int col) {
    _cell(row, col, 'queen');
  }

  /// The whole board is wrapped in a single GestureDetector.
  /// We translate (dx,dy) → (row,col) from the board's top-left.
  void _onPanStart(Offset local, double cellSize) {
    _isPan = false;
    _pannedCells.clear();
    final (row, col) = _pos2cell(local, cellSize);
    if (row < 0) return;
    _isPan = true;
    final k = '$row,$col';
    _pannedCells.add(k);
    // Don't cross on pan-start — wait for a second cell to confirm it's a drag
  }

  void _onPanUpdate(Offset local, double cellSize) {
    if (!_isPan) return;
    final (row, col) = _pos2cell(local, cellSize);
    if (row < 0) return;
    final k = '$row,$col';
    if (!_pannedCells.contains(k)) {
      _pannedCells.add(k);
      _cell(row, col, 'cross');
    }
  }

  void _onPanEnd() {
    // If only 1 cell panned → it was actually a tap, handled by onTap
    _isPan = false;
    _pannedCells.clear();
  }

  (int, int) _pos2cell(Offset local, double cs) {
    final n = widget.boardSize;
    final col = (local.dx / cs).floor();
    final row = (local.dy / cs).floor();
    if (row < 0 || row >= n || col < 0 || col >= n) return (-1, -1);
    return (row, col);
  }

  // ─────────────────────────────────────────────────────────────
  // HELPERS
  // ─────────────────────────────────────────────────────────────
  List<List<int>> get _boardData {
    final raw = _game!['board'] as List;
    return raw.map((r) => (r as List).map((c) => c as int).toList()).toList();
  }

  List<List<int>> get _regData {
    final raw = _game!['regions'] as List;
    return raw.map((r) => (r as List).map((c) => c as int).toList()).toList();
  }

  Set<String> get _errSet {
    final v = _game?['validation'];
    if (v == null) return {};
    final cells = v['error_cells'];
    if (cells == null) return {};
    return {for (final c in cells as List) '${c[0]},${c[1]}'};
  }

  String _fmt(int s) {
    final m = s ~/ 60, sec = s % 60;
    return '${m.toString().padLeft(2,'0')}:${sec.toString().padLeft(2,'0')}';
  }

  void _snack(String msg) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(
      content: Text(msg), backgroundColor: _errC,
      behavior: SnackBarBehavior.floating, duration: const Duration(seconds: 3),
    ));
  }

  void _winDialog(Map<String, dynamic> g) {
    if (!mounted) return;
    final rank  = g['rank_position'];
    final moves = g['move_count'] ?? 0;
    Future.delayed(const Duration(milliseconds: 400), () {
      if (!mounted) return;
      showDialog(
        context: context, barrierDismissible: false,
        builder: (_) => AlertDialog(
          backgroundColor: _surface,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
          title: const Row(children: [
            Icon(Icons.workspace_premium_rounded, color: _accent, size: 28),
            SizedBox(width: 8),
            Text('¡Completado!', style: TextStyle(color: _textP, fontSize: 20)),
          ]),
          content: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
            _WR('Tiempo', _fmt(_elapsed)),
            _WR('Movimientos', moves.toString()),
            if (rank != null) _WR('Posición', '#$rank'),
          ]),
          actions: [
            TextButton(onPressed: () { Navigator.pop(context); Navigator.pop(context); },
              child: const Text('Menú', style: TextStyle(color: _textS))),
            ElevatedButton(
              style: ElevatedButton.styleFrom(backgroundColor: _accent),
              onPressed: () { Navigator.pop(context); _newGame(); },
              child: const Text('Nuevo juego', style: TextStyle(color: Colors.black))),
          ],
        ),
      );
    });
  }

  void _showRecords() async {
    showDialog(context: context, builder: (_) => const _Busy('Cargando récords…'));
    try {
      final data = await ApiService.getRecords(widget.boardSize);
      if (!mounted) return;
      Navigator.pop(context);
      final records = (data['records'] as List?) ?? [];
      showDialog(
        context: context,
        builder: (_) => AlertDialog(
          backgroundColor: _surface,
          title: Text('Top 10 — ${widget.boardSize}×${widget.boardSize}',
              style: const TextStyle(color: _textP)),
          content: records.isEmpty
              ? const Text('Sin récords aún.', style: TextStyle(color: _textS))
              : SizedBox(width: double.maxFinite,
                  child: ListView.separated(
                    shrinkWrap: true, itemCount: records.length,
                    separatorBuilder: (_, __) => const Divider(color: Color(0xFF334155)),
                    itemBuilder: (_, i) {
                      final r = records[i] as Map;
                      return ListTile(
                        leading: CircleAvatar(
                          backgroundColor: _accent.withAlpha(40),
                          child: Text('${i+1}', style: const TextStyle(color: _accent, fontWeight: FontWeight.bold)),
                        ),
                        title:    Text(r['time_formatted']?.toString() ?? '-', style: const TextStyle(color: _textP)),
                        subtitle: Text('${r['moves']} movimientos',            style: const TextStyle(color: _textS)),
                      );
                    },
                  )),
          actions: [TextButton(onPressed: () => Navigator.pop(context),
              child: const Text('Cerrar', style: TextStyle(color: _accent)))],
        ),
      );
    } catch (e) {
      if (mounted) { Navigator.pop(context); _snack(e.toString()); }
    }
  }

  void _showRules() async {
    showDialog(context: context, builder: (_) => const _Busy('Cargando reglas…'));
    try {
      final data = await ApiService.getRules();
      if (!mounted) return;
      Navigator.pop(context);
      final rules = (data['rules'] as List?) ?? [];
      showDialog(
        context: context,
        builder: (_) => AlertDialog(
          backgroundColor: _surface,
          title: const Text('Reglas', style: TextStyle(color: _textP)),
          content: SizedBox(width: double.maxFinite,
            child: ListView.builder(shrinkWrap: true, itemCount: rules.length,
              itemBuilder: (_, i) => Padding(
                padding: const EdgeInsets.symmetric(vertical: 4),
                child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  const Text('• ', style: TextStyle(color: _accent, fontSize: 16)),
                  Expanded(child: Text(rules[i].toString(), style: const TextStyle(color: _textP, fontSize: 14))),
                ]),
              ),
            )),
          actions: [TextButton(onPressed: () => Navigator.pop(context),
              child: const Text('Cerrar', style: TextStyle(color: _accent)))],
        ),
      );
    } catch (e) {
      if (mounted) { Navigator.pop(context); _snack(e.toString()); }
    }
  }

  // ─────────────────────────────────────────────────────────────
  // BUILD
  // ─────────────────────────────────────────────────────────────
  @override
  Widget build(BuildContext context) => Scaffold(
    backgroundColor: _bg,
    appBar: AppBar(
      backgroundColor: _surface,
      title: Text('${widget.boardSize}×${widget.boardSize} Queens',
          style: const TextStyle(color: _textP, fontWeight: FontWeight.bold)),
      iconTheme: const IconThemeData(color: _textS),
      actions: [
        IconButton(icon: const Icon(Icons.emoji_events_outlined), tooltip: 'Récords', onPressed: _showRecords),
        IconButton(icon: const Icon(Icons.help_outline_rounded),  tooltip: 'Reglas',  onPressed: _showRules),
      ],
    ),
    body: _loading ? const Center(child: CircularProgressIndicator(color: _accent))
        : _error != null ? _ErrView(error: _error!, onRetry: _newGame)
        : _buildGame(),
  );

  Widget _buildGame() {
    final won = _game!['is_won'] == true;
    return Column(children: [
      _statusBar(won),
      Expanded(child: Padding(padding: const EdgeInsets.all(10), child: _buildBoard())),
      _controls(won),
      const SizedBox(height: 6),
    ]);
  }

  Widget _statusBar(bool won) => Container(
    color: _surface,
    padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
    child: Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
      Row(children: [
        const Icon(Icons.timer_outlined, color: _textS, size: 18),
        const SizedBox(width: 6),
        Text(_fmt(_elapsed), style: TextStyle(
          color: won ? _winC : _textP, fontSize: 20, fontWeight: FontWeight.bold,
          fontFeatures: const [FontFeature.tabularFigures()])),
      ]),
      Row(children: [
        const Text('Auto-X', style: TextStyle(color: _textS, fontSize: 13)),
        const SizedBox(width: 4),
        Switch(value: _autoCross, onChanged: (_) => _toggleAuto(),
            activeColor: _accent, materialTapTargetSize: MaterialTapTargetSize.shrinkWrap),
      ]),
    ]),
  );

  Widget _buildBoard() {
    final n    = widget.boardSize;
    final board = _boardData;
    final regs  = _regData;
    final errs  = _errSet;

    return AspectRatio(
      aspectRatio: 1,
      child: LayoutBuilder(builder: (ctx, box) {
        final cs = box.maxWidth / n;
        return GestureDetector(
          behavior: HitTestBehavior.opaque,
          // ── Drag: crosses on all visited cells ───────────────
          onPanStart:  (d) => _onPanStart(d.localPosition, cs),
          onPanUpdate: (d) => _onPanUpdate(d.localPosition, cs),
          onPanEnd:    (_) => _onPanEnd(),
          // ── Tap & DoubleTap ──────────────────────────────────
          onTapUp: (d) {
            final (row, col) = _pos2cell(d.localPosition, cs);
            if (row < 0) return;
            final now = DateTime.now();
            if (_lastTapTime != null &&
                now.difference(_lastTapTime!) < _doubleTapWindow &&
                _lastTapRow == row && _lastTapCol == col) {
              // Double tap detected
              _lastTapTime = null;
              _onDoubleTap(row, col);
            } else {
              _lastTapTime = now;
              _lastTapRow  = row;
              _lastTapCol  = col;
              // Delay single-tap to give double-tap a chance to cancel it
              Future.delayed(_doubleTapWindow, () {
                if (_lastTapTime == now) {
                  _onSingleTap(row, col);
                }
              });
            }
          },
          child: SizedBox(
            width:  cs * n,
            height: cs * n,
            child: GridView.builder(
              physics: const NeverScrollableScrollPhysics(),
              gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(crossAxisCount: n),
              itemCount: n * n,
              itemBuilder: (_, idx) {
                final row = idx ~/ n, col = idx % n;
                final state  = board[row][col];
                final region = regs[row][col];
                final err    = errs.contains('$row,$col');
                final base   = _rc(region);
                final cellColor = err ? Color.lerp(base, _errC, 0.45)! : base;
                return Container(
                  decoration: BoxDecoration(
                    color: cellColor,
                    border: Border.all(color: Colors.black.withAlpha(55), width: 0.5),
                    boxShadow: err ? [BoxShadow(color: _errC.withAlpha(90), blurRadius: 4)] : null,
                  ),
                  child: Center(child: _icon(state, cs)),
                );
              },
            ),
          ),
        );
      }),
    );
  }

  Widget? _icon(int state, double cs) {
    final s = cs * 0.54;
    if (state == 1) return Icon(Icons.workspace_premium_rounded, color: const Color(0xFF1E293B), size: s);
    if (state == 2) return Icon(Icons.close_rounded,             color: const Color(0xFF64748B), size: s * 0.82);
    return null;
  }

  Widget _controls(bool won) => Padding(
    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
    child: Row(mainAxisAlignment: MainAxisAlignment.spaceEvenly, children: [
      _Btn(Icons.undo_rounded,           'Deshacer', won ? null : _undo),
      _Btn(Icons.refresh_rounded,        'Reiniciar', won ? null : _reset),
      _Btn(Icons.lightbulb_outline_rounded, 'Pista',  won ? null : _hint),
      _Btn(Icons.add_circle_outline_rounded, 'Nuevo', _newGame, color: _accent),
    ]),
  );
}

// ─────────────────────────────────────────────────────────────────
// SMALL WIDGETS
// ─────────────────────────────────────────────────────────────────
class _WR extends StatelessWidget {
  final String label, value;
  const _WR(this.label, this.value);
  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 4),
    child: Row(children: [
      Text('$label: ', style: const TextStyle(color: _textS, fontSize: 15)),
      Text(value, style: const TextStyle(color: _winC, fontSize: 15, fontWeight: FontWeight.bold)),
    ]),
  );
}

class _Btn extends StatelessWidget {
  final IconData icon; final String label;
  final VoidCallback? onPressed; final Color? color;
  const _Btn(this.icon, this.label, this.onPressed, {this.color});
  @override
  Widget build(BuildContext context) {
    final c = color ?? _textS;
    return TextButton(
      onPressed: onPressed,
      style: TextButton.styleFrom(
        foregroundColor: c,
        disabledForegroundColor: c.withAlpha(60),
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
      ),
      child: Column(mainAxisSize: MainAxisSize.min, children: [
        Icon(icon, size: 22),
        const SizedBox(height: 2),
        Text(label, style: const TextStyle(fontSize: 11)),
      ]),
    );
  }
}

class _Busy extends StatelessWidget {
  final String message;
  const _Busy(this.message);
  @override
  Widget build(BuildContext context) => AlertDialog(
    backgroundColor: _surface,
    content: Row(children: [
      const CircularProgressIndicator(color: _accent),
      const SizedBox(width: 16),
      Text(message, style: const TextStyle(color: _textP)),
    ]),
  );
}

class _ErrView extends StatelessWidget {
  final String error; final VoidCallback onRetry;
  const _ErrView({required this.error, required this.onRetry});
  @override
  Widget build(BuildContext context) => Center(
    child: Padding(padding: const EdgeInsets.all(32),
      child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
        const Icon(Icons.cloud_off_rounded, color: _errC, size: 56),
        const SizedBox(height: 16),
        const Text('No se pudo conectar con el servidor',
            textAlign: TextAlign.center,
            style: TextStyle(color: _textP, fontSize: 16)),
        const SizedBox(height: 8),
        Text(error, textAlign: TextAlign.center, style: const TextStyle(color: _textS, fontSize: 13)),
        const SizedBox(height: 24),
        ElevatedButton.icon(
          style: ElevatedButton.styleFrom(backgroundColor: _accent),
          icon: const Icon(Icons.refresh_rounded, color: Colors.black),
          label: const Text('Reintentar', style: TextStyle(color: Colors.black)),
          onPressed: onRetry,
        ),
      ]),
    ),
  );
}
