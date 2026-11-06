import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

void main() {
  runApp(const UmrohAdvisorApp());
}

class UmrohAdvisorApp extends StatelessWidget {
  const UmrohAdvisorApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Umroh Aspect Sentiment Evaluator',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.teal),
        useMaterial3: true,
      ),
      home: const HomeScreen(),
      debugShowCheckedModeBanner: false,
    );
  }
}

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final TextEditingController _urlController = TextEditingController();
  bool _isLoading = false;
  String? _errorMessage;
  Map<String, dynamic>? _resultData;

  Future<void> _analyzeTravel() async {
    final url = _urlController.text.trim();
    if (url.isEmpty) {
      setState(() => _errorMessage = "Silakan masukkan tautan Google Maps travel.");
      return;
    }

    setState(() {
      _isLoading = true;
      _errorMessage = null;
      _resultData = null;
    });

    // Gunakan 127.0.0.1 jika dijalankan di Chrome Desktop, atau 10.0.2.2 jika di Android Emulator
    final uri = Uri.parse("http://127.0.0.1:8000/api/v1/analyze-travel");

    try {
      final response = await http.post(
        uri,
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({"google_maps_url": url}),
      );

      if (response.statusCode == 200) {
        setState(() {
          _resultData = jsonDecode(response.body);
        });
      } else {
        setState(() {
          _errorMessage = "Gagal memproses data (Error HTTP ${response.statusCode})";
        });
      }
    } catch (e) {
      setState(() {
        _errorMessage = "Gagal menghubungi server lokal. Pastikan FastAPI sedang running.";
      });
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Widget _buildAspectBar(String aspectName, Map<String, dynamic> data) {
    final double pos = (data['positif'] as num).toDouble();
    final double net = (data['netral'] as num).toDouble();
    final double neg = (data['negatif'] as num).toDouble();

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                aspectName.replaceAll("_", " "),
                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
              ),
              Text(
                "Prediksi: ${data['prediksi_tertinggi']}",
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.bold,
                  color: data['prediksi_tertinggi'] == 'Positif'
                      ? Colors.green
                      : (data['prediksi_tertinggi'] == 'Negatif' ? Colors.red : Colors.orange),
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          ClipRRect(
            borderRadius: BorderRadius.circular(6),
            child: Row(
              children: [
                Expanded(
                  flex: pos > 0 ? (pos * 10).toInt() : 1,
                  child: Container(height: 14, color: Colors.green),
                ),
                Expanded(
                  flex: net > 0 ? (net * 10).toInt() : 1,
                  child: Container(height: 14, color: Colors.amber),
                ),
                Expanded(
                  flex: neg > 0 ? (neg * 10).toInt() : 1,
                  child: Container(height: 14, color: Colors.redAccent),
                ),
              ],
            ),
          ),
          const SizedBox(height: 4),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text("Positif: ${pos.toStringAsFixed(1)}%", style: const TextStyle(fontSize: 11, color: Colors.green)),
              Text("Netral: ${net.toStringAsFixed(1)}%", style: TextStyle(fontSize: 11, color: Colors.amber[800])),
              Text("Negatif: ${neg.toStringAsFixed(1)}%", style: const TextStyle(fontSize: 11, color: Colors.red)),
            ],
          ),
          const Divider(height: 16),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Rekomendasi Travel Umroh"),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            TextField(
              controller: _urlController,
              decoration: const InputDecoration(
                labelText: "Tautan Google Maps Travel Umroh",
                hintText: "https://maps.app.goo.gl/...",
                prefixIcon: Icon(Icons.link),
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 12),
            ElevatedButton(
              onPressed: _isLoading ? null : _analyzeTravel,
              style: ElevatedButton.styleFrom(padding: const EdgeInsets.all(14)),
              child: _isLoading
                  ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(strokeWidth: 2))
                  : const Text("Analisis Reputasi 6 Aspek"),
            ),
            if (_errorMessage != null) ...[
              const SizedBox(height: 16),
              Text(_errorMessage!, style: const TextStyle(color: Colors.red, fontWeight: FontWeight.bold)),
            ],
            if (_resultData != null) ...[
              const SizedBox(height: 20),
              Card(
                elevation: 3,
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        _resultData!['travel_name'],
                        style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 4),
                      Text("Total Ulasan: ${_resultData!['total_reviews_analyzed']}"),
                      const Divider(height: 24),
                      const Text(
                        "Distribusi Sentimen per Aspek Layanan:",
                        style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                      ),
                      const SizedBox(height: 10),
                      ...(_resultData!['sentiment_analysis_summary'] as Map<String, dynamic>)
                          .entries
                          .map((e) => _buildAspectBar(e.key, e.value)),
                    ],
                  ),
                ),
              ),
            ]
          ],
        ),
      ),
    );
  }
}