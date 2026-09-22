with open('dashboard/static/js/dashboard.js', 'a', encoding='utf-8') as f:
    f.write('''
        function updateWeatherUI(data) {
            var out = data.outdoor || {};
            var deltaTemp = out.delta_temperature || 0;
            var deltaHum  = out.delta_humidity || 0;

            var tempEl = document.getElementById('weather-temp');
            var humEl  = document.getElementById('weather-humidity');
            var descEl = document.getElementById('weather-desc');

            if (tempEl && out.temperature !== null) {
                tempEl.textContent = out.temperature + ' C';
            }
            if (humEl && out.humidity !== null) {
                humEl.textContent = out.humidity + '%';
            }
            if (descEl && out.weather_desc) {
                descEl.textContent = out.weather_desc;
            }

            var tempBadge = document.getElementById('weather-temp-badge');
            if (tempBadge && out.temperature !== null) {
                var absTemp = Math.abs(deltaTemp).toFixed(1);
                if (deltaTemp > 0.5) {
                    tempBadge.textContent = 'Lebih panas +' + absTemp + ' C';
                    tempBadge.style.background = 'rgba(239,68,68,0.15)';
                    tempBadge.style.color = '#ef4444';
                } else if (deltaTemp < -0.5) {
                    tempBadge.textContent = 'Lebih dingin -' + absTemp + ' C';
                    tempBadge.style.background = 'rgba(14,165,233,0.18)';
                    tempBadge.style.color = '#0ea5e9';
                } else {
                    tempBadge.textContent = '= Sama';
                    tempBadge.style.background = 'rgba(16,185,129,0.15)';
                    tempBadge.style.color = '#10b981';
                }
            }

            var humBadge = document.getElementById('weather-humidity-badge');
            if (humBadge && out.humidity !== null) {
                var absHum = Math.abs(deltaHum).toFixed(0);
                if (deltaHum > 5) {
                    humBadge.textContent = 'Lebih lembab +' + absHum + '%';
                    humBadge.style.background = 'rgba(14,165,233,0.18)';
                    humBadge.style.color = '#0ea5e9';
                } else if (deltaHum < -5) {
                    humBadge.textContent = 'Lebih lembab +' + absHum + '%';
                    humBadge.style.background = 'rgba(239,68,68,0.15)';
                    humBadge.style.color = '#ef4444';
                } else {
                    humBadge.textContent = '= Sama';
                    humBadge.style.background = 'rgba(16,185,129,0.15)';
                    humBadge.style.color = '#10b981';
                }
            }

            var statusBadge = document.getElementById('weather-status-badge');
            if (statusBadge) {
                if (out.fetch_ok) {
                    statusBadge.textContent = 'Online';
                    statusBadge.style.background = 'rgba(16,185,129,0.12)';
                    statusBadge.style.color = '#10b981';
                } else {
                    statusBadge.textContent = 'Offline';
                    statusBadge.style.background = 'rgba(239,68,68,0.12)';
                    statusBadge.style.color = '#ef4444';
                }
            }

            var insightEl = document.getElementById('weather-insight-text');
            if (insightEl && out.temperature !== null) {
                var insights = [];
                var tempO = out.temperature;
                var humO  = out.humidity;
                var uvO   = out.uv_index;
                var rainO = out.precipitation;
                var windO = out.wind_speed;
                var desc  = out.weather_desc || '';

                if (rainO > 0) {
                    insights.push('Hujan ' + rainO + 'mm terdeteksi - pastikan ventilasi tertutup untuk menjaga kelembaban ruangan.');
                } else if (tempO > 33) {
                    insights.push('Suhu luar sangat panas (' + tempO + ' C) - AC bekerja lebih keras. GA akan merekomendasikan setpoint lebih rendah.');
                } else if (tempO > 28 && deltaTemp < 0) {
                    insights.push('Cuaca panas di luar (' + tempO + ' C) - ruangan Anda lebih dingin. AC berjalan optimal.');
                } else if (tempO < 25) {
                    insights.push('Cuaca sejuk di luar (' + tempO + ' C) - pertimbangkan membuka ventilasi untuk hemat energi.');
                }
                if (uvO >= 8) {
                    insights.push('Indeks UV sangat tinggi (' + uvO + ') - hindari paparan sinar matahari langsung.');
                } else if (uvO >= 5) {
                    insights.push('Indeks UV tinggi (' + uvO + ') - gunakan perlindungan jika berada di luar.');
                }
                if (humO > 85) {
                    insights.push('Kelembaban luar sangat tinggi (' + humO + '%) - potensi kondensasi pada kaca jendela.');
                }
                if (windO > 30) {
                    insights.push('Angin kencang (' + windO + ' km/h) terdeteksi di area UNS.');
                }

                insightEl.textContent = insights.length > 0
                    ? insights[0]
                    : 'Kondisi cuaca ' + (desc || 'normal') + ' di UNS Surakarta. Suhu luar: ' + tempO + ' C, Kelembaban: ' + humO + '%.';
            }
        }

        function fetchOutdoorWeather(retryCount) {
            retryCount = retryCount || 0;
            var MAX_RETRIES = 3;
            fetch('/api/outdoor-weather')
                .then(function(r) {
                    if (!r.ok) throw new Error('HTTP ' + r.status);
                    return r.json();
                })
                .then(function(data) {
                    try {
                        updateWeatherUI(data);
                        var out = data.outdoor || {};
                        if (!out.fetch_ok && out.temperature === null) {
                            var descEl = document.getElementById('weather-desc');
                            if (descEl) descEl.textContent = 'Menunggu data...';
                            var insightEl = document.getElementById('weather-insight-text');
                            if (insightEl) insightEl.textContent = 'Server belum bisa mengakses Open-Meteo API. Periksa koneksi internet server.';
                            setTimeout(function() { fetchOutdoorWeather(0); }, 15000);
                        }
                    } catch(e) {
                        console.warn('[WEATHER] UI update error:', e);
                    }
                })
                .catch(function(e) {
                    console.warn('[WEATHER] Fetch failed (attempt ' + (retryCount+1) + '):', e.message);
                    if (retryCount < MAX_RETRIES) {
                        var delay = (retryCount + 1) * 3000;
                        setTimeout(function() { fetchOutdoorWeather(retryCount + 1); }, delay);
                        return;
                    }
                    var statusBadge = document.getElementById('weather-status-badge');
                    if (statusBadge) {
                        statusBadge.textContent = 'Error';
                        statusBadge.style.background = 'rgba(239,68,68,0.12)';
                        statusBadge.style.color = '#ef4444';
                    }
                    var descEl = document.getElementById('weather-desc');
                    if (descEl) descEl.textContent = 'Tidak tersedia';
                    var insightEl = document.getElementById('weather-insight-text');
                    if (insightEl) insightEl.textContent = 'Gagal memuat cuaca setelah 3x percobaan. Periksa koneksi internet server atau klik tombol refresh.';
                    setTimeout(function() { fetchOutdoorWeather(0); }, 30000);
                });
        }

        function refreshOutdoorWeather() {
            var btn = document.querySelector(\'[onclick="refreshOutdoorWeather()"]\');
            if (btn) { btn.style.opacity = '0.4'; btn.style.pointerEvents = 'none'; }
            var statusBadge = document.getElementById('weather-status-badge');
            if (statusBadge) {
                statusBadge.textContent = 'Memuat';
                statusBadge.style.background = 'rgba(148,163,184,0.12)';
                statusBadge.style.color = '#94a3b8';
            }
            fetchOutdoorWeather(0);
            setTimeout(function() {
                if (btn) { btn.style.opacity = '1'; btn.style.pointerEvents = 'auto'; }
            }, 2000);
        }

        setTimeout(fetchOutdoorWeather, 800);
        _weatherRefreshTimer = setInterval(fetchOutdoorWeather, 600000);
''')
