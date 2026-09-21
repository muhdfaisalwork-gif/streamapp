import 'dart:async';
import 'package:flutter/material.dart';
import '../models/models.dart';
import '../services/api_service.dart';
import '../theme/app_theme.dart';
import '../widgets/media_card.dart';
import '../widgets/responsive_layout.dart';

class SearchScreen extends StatefulWidget {
  final ApiService apiService;
  final Function(MediaItem) onSelectMedia;

  const SearchScreen({
    Key? key,
    required this.apiService,
    required this.onSelectMedia,
  }) : super(key: key);

  @override
  State<SearchScreen> createState() => _SearchScreenState();
}

class _SearchScreenState extends State<SearchScreen> {
  final TextEditingController _controller = TextEditingController();
  Timer? _debounce;
  List<MediaItem> _results = [];
  bool _isLoading = false;
  String _selectedGenre = 'All';

  final List<String> _genres = ['All', 'Animation', 'Sci-Fi', 'Horror', 'Classic', 'Fantasy', 'Action'];

  @override
  void initState() {
    super.initState();
    _performSearch('');
  }

  void _onQueryChanged(String query) {
    _debounce?.cancel();
    _debounce = Timer(const Duration(milliseconds: 300), () {
      _performSearch(query);
    });
  }

  void _performSearch(String query) async {
    setState(() => _isLoading = true);
    var results = await widget.apiService.search(query);
    if (_selectedGenre != 'All') {
      results = results.where((m) => m.genres.contains(_selectedGenre)).toList();
    }
    setState(() {
      _results = results;
      _isLoading = false;
    });
  }

  @override
  void dispose() {
    _debounce?.cancel();
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final isPhone = ResponsiveLayout.isPhone(context);
    final isTablet = ResponsiveLayout.isTablet(context);
    final columns = isPhone ? 2 : (isTablet ? 3 : 5);

    return Scaffold(
      backgroundColor: AppTheme.bgCanvas,
      appBar: AppBar(
        title: TextField(
          controller: _controller,
          autofocus: true,
          onChanged: _onQueryChanged,
          style: const TextStyle(color: AppTheme.textPrimary),
          decoration: InputDecoration(
            hintText: 'Search movies, genres, creators...',
            hintStyle: const TextStyle(color: AppTheme.textMuted),
            prefixIcon: const Icon(Icons.search, color: AppTheme.brandPrimary),
            suffixIcon: _controller.text.isNotEmpty
                ? IconButton(
                    icon: const Icon(Icons.clear, color: AppTheme.textSecondary),
                    onPressed: () {
                      _controller.clear();
                      _performSearch('');
                    },
                  )
                : null,
            filled: true,
            fillColor: AppTheme.bgSurface2,
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(AppTheme.radiusMd),
              borderSide: BorderSide.none,
            ),
            contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          ),
        ),
      ),
      body: Column(
        children: [
          // Genre Filter Chips Row
          SizedBox(
            height: 48,
            child: ListView.builder(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: AppTheme.space4, vertical: 6),
              itemCount: _genres.length,
              itemBuilder: (context, index) {
                final genre = _genres[index];
                final isSelected = _selectedGenre == genre;
                return Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: FilterChip(
                    label: Text(genre),
                    selected: isSelected,
                    selectedColor: AppTheme.brandPrimary,
                    labelStyle: TextStyle(
                      color: isSelected ? AppTheme.bgCanvas : AppTheme.textPrimary,
                      fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                    ),
                    backgroundColor: AppTheme.bgSurface2,
                    onSelected: (selected) {
                      setState(() => _selectedGenre = genre);
                      _performSearch(_controller.text);
                    },
                  ),
                );
              },
            ),
          ),

          // Results Grid
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : _results.isEmpty
                    ? Center(
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            const Icon(Icons.search_off, size: 54, color: AppTheme.textMuted),
                            const SizedBox(height: AppTheme.space2),
                            const Text('No titles matched your search', style: TextStyle(color: AppTheme.textSecondary, fontSize: 16)),
                            const SizedBox(height: AppTheme.space1),
                            const Text('Try searching for "Sintel", "Blender", or "Horror"', style: TextStyle(color: AppTheme.textMuted, fontSize: 13)),
                          ],
                        ),
                      )
                    : GridView.builder(
                        padding: const EdgeInsets.all(AppTheme.space4),
                        gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                          crossAxisCount: columns,
                          childAspectRatio: 16 / 11,
                          crossAxisSpacing: 12,
                          mainAxisSpacing: 12,
                        ),
                        itemCount: _results.length,
                        itemBuilder: (context, index) {
                          final item = _results[index];
                          return MediaCard(
                            item: item,
                            aspectRatio: MediaCardAspectRatio.landscape16x9,
                            onTap: () => widget.onSelectMedia(item),
                          );
                        },
                      ),
          ),
        ],
      ),
    );
  }
}
