"use client";

import { FormEvent, useState } from "react";

import { useAuth } from "@/lib/auth";
import type { UserRole } from "@/types";

export default function LoginPage() {
  const { login, register } = useAuth();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [role, setRole] = useState<UserRole>("startup");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const email = String(form.get("email") ?? "");
    const password = String(form.get("password") ?? "");
    setBusy(true);
    setError("");
    try {
      if (mode === "login") await login(email, password);
      else await register({ email, password, full_name: String(form.get("full_name") ?? ""), role });
      window.location.href = "/";
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không thể đăng nhập");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="authPage">
      <section className="surface authCard">
        <div>
          <p className="eyebrow">STARTUP LENS</p>
          <h1>{mode === "login" ? "Đăng nhập" : "Tạo tài khoản"}</h1>
          <p className="muted">Dữ liệu và chức năng sẽ được giới hạn theo đúng vai trò của bạn.</p>
        </div>
        <div className="segmentedControl authMode">
          <button className={mode === "login" ? "active" : ""} onClick={() => setMode("login")} type="button">Đăng nhập</button>
          <button className={mode === "register" ? "active" : ""} onClick={() => setMode("register")} type="button">Đăng ký</button>
        </div>
        {error && <div className="alert">{error}</div>}
        <form className="stackForm" onSubmit={submit}>
          {mode === "register" && (
            <>
              <label>Họ và tên<input name="full_name" minLength={2} required /></label>
              <label>
                Vai trò
                <select value={role} onChange={(event) => setRole(event.target.value as UserRole)}>
                  <option value="startup">Startup</option>
                  <option value="investor">Nhà đầu tư</option>
                </select>
              </label>
            </>
          )}
          <label>Email<input name="email" type="email" required /></label>
          <label>Mật khẩu<input name="password" type="password" minLength={8} required /></label>
          <button className="primaryButton" disabled={busy}>
            {busy ? "Đang xử lý..." : mode === "login" ? "Đăng nhập" : "Tạo tài khoản"}
          </button>
        </form>
      </section>
    </div>
  );
}
