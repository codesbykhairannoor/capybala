"""
Llama-Doctor: Runtime Deadlock Breaker & Context Recovery Guardrail for Autonomous Llama Agents
Meta Global AI Developer Hackathon 2026 Submission Component
"""

import re
from typing import List, Dict, Tuple, Optional

class LlamaDoctor:
    def __init__(self, repetition_threshold: int = 3, similarity_threshold: float = 0.85):
        """
        LlamaDoctor mengawasi eksekusi agen Llama secara real-time.
        Jika agen mulai mengulang perintah terminal yang gagal, LlamaDoctor
        menginterupsi eksekusi, memangkas context yang kotor, dan memberikan arahan baru.
        """
        self.repetition_threshold = repetition_threshold
        self.similarity_threshold = similarity_threshold
        self.action_history: List[str] = []
        self.observation_history: List[str] = []
        self.total_tokens_saved: int = 0
        self.interventions_count: int = 0

    def _normalize_command(self, cmd: str) -> str:
        """Menghapus whitespace dan argumen dinamis sederhana untuk deteksi pola"""
        cmd_clean = re.sub(r"\s+", " ", cmd.strip().lower())
        return cmd_clean

    def check_deadlock(self, current_action: str, last_observation: str) -> Tuple[bool, Optional[str]]:
        """
        Menganalisis apakah tindakan saat ini merupakan bagian dari Cognitive Deadlock
        """
        norm_cmd = self._normalize_command(current_action)
        self.action_history.append(norm_cmd)
        self.observation_history.append(last_observation)

        # 1. Hitung berapa kali perintah yang mirip diulang belakangan ini
        recent_actions = self.action_history[-6:]
        repetition_count = recent_actions.count(norm_cmd)

        # 2. Cek apakah feedback lingkungan berisi Traceback/Error
        is_error = any(err in last_observation for err in ["Traceback", "Error", "FAILED", "Exception", "not found"])

        if repetition_count >= self.repetition_threshold and is_error:
            self.interventions_count += 1
            return True, f"Cognitive Deadlock Detected: Command '{norm_cmd}' repeated {repetition_count}x with persistent terminal errors."

        return False, None

    def rescue_agent(self, conversation_history: List[Dict[str, str]], deadlock_reason: str) -> Tuple[List[Dict[str, str]], str]:
        """
        AKSI PENYELAMATAN (Self-Healing Intervention):
        1. Context Pruning: Hapus jejak 4 traceback error berulang yang membakar context window.
        2. Strategic Guidance Injection: Berikan instruksi baru agar Llama keluar dari jalan buntu.
        """
        # Hitung perkiraan token yang diselamatkan dari context overflow
        estimated_chars_pruned = sum(len(msg.get("content", "")) for msg in conversation_history[-4:])
        self.total_tokens_saved += int(estimated_chars_pruned / 4)

        # 1. Pangkas percakapan terakhir yang berulang
        pruned_history = conversation_history[:-4]

        # 2. Suntikkan corrective prompt dari Supervisor Llama-Doctor
        doctor_hint = (
            f"[LLAMA-DOCTOR RESCUE INTERVENTION]\n"
            f"Perhatian: Anda terdeteksi mengalami kebuntuan penalaran ({deadlock_reason}).\n"
            f"Tindakan Anda sebelumnya gagal berulang kali karena pendekatan yang sama.\n"
            f"INSTRUKSI: HENTIKAN perintah tersebut segera! Beralihlah ke pendekatan alternatif:\n"
            f"1. Baca kembali file konfigurasi atau import path dari root repositori.\n"
            f"2. Jangan ulangi eksekusi script yang sama sebelum memperbaiki dependensi dasar.\n"
            f"Silakan rumuskan hipotesis baru yang sama sekali berbeda."
        )

        pruned_history.append({"role": "system", "content": doctor_hint})
        return pruned_history, doctor_hint


# === DEMO SIMULASI PENYELAMATAN AGENT PADA RUNTIME ===
if __name__ == "__main__":
    print("=" * 65)
    print("DEMO RUNTIME LLAMA-DOCTOR: MEMUTUS LOOP ERROR PADA AGEN LLAMA-3")
    print("=" * 65)

    doctor = LlamaDoctor(repetition_threshold=3)

    # Simulasi history percakapan agen Llama
    agent_conversation = [
        {"role": "user", "content": "Tolong perbaiki bug import di module auth.py"}
    ]

    # Perintah yang diulang-ulang oleh Llama saat panik
    failing_command = "python -m pytest tests/test_auth.py"
    terminal_error = "Traceback (most recent call last): ModuleNotFoundError: No module named 'jwt'"

    print("\n[Simulasi Eksekusi Langkah Agen Llama]:")
    for step in range(1, 5):
        print(f"\n--- Turn {step} ---")
        print(f"Llama Action : `{failing_command}`")
        print(f"Terminal     : {terminal_error[:65]}...")

        agent_conversation.append({"role": "assistant", "content": f"Saya coba jalankan: {failing_command}"})
        agent_conversation.append({"role": "user", "content": terminal_error})

        # LlamaDoctor memantau tiap langkah secara real-time
        is_deadlocked, reason = doctor.check_deadlock(failing_command, terminal_error)

        if is_deadlocked:
            print(f"\n[ALERT DETECTED]: {reason}")
            print("[LLAMA-DOCTOR ACTIVATED]: Menginterupsi agen Llama secara paksa!")
            
            rescued_history, hint = doctor.rescue_agent(agent_conversation, reason)
            
            print("\n[Hasil Penyelamatan]:")
            print(f"[OK] Context Beracun Berhasil Dipangkas: {len(agent_conversation)} turns -> {len(rescued_history)} turns")
            print(f"[OK] Estimasi Token Diselamatkan: ~{doctor.total_tokens_saved} tokens")
            print("\n[Pesan Korektif yang Disuntikkan ke Llama]:")
            print(hint)
            print("\n[STATUS]: Agen berhasil diselamatkan dari kematian context overflow!")
            break
        else:
            print("Status Guardrail: Normal (Belum mencapai batas threshold loop)")
