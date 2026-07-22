import { Route, Routes } from "react-router-dom";
import { AdminRoute } from "./auth/AdminRoute";
import { AdminLayout } from "./components/AdminLayout";
import { AuditPage } from "./pages/AuditPage";
import { DashboardPage } from "./pages/DashboardPage";
import { DepositDetailsPage } from "./pages/DepositDetailsPage";
import { DepositsPage } from "./pages/DepositsPage";
import { LoginPage } from "./pages/LoginPage";
import { NotFoundPage } from "./pages/NotFoundPage";
import { PlanFormPage } from "./pages/PlanFormPage";
import { PlansPage } from "./pages/PlansPage";
import { PostFormPage } from "./pages/PostFormPage";
import { PostsPage } from "./pages/PostsPage";
import { SupportDetailsPage } from "./pages/SupportDetailsPage";
import { SupportPage } from "./pages/SupportPage";
import { UserDetailsPage } from "./pages/UserDetailsPage";
import { UsersPage } from "./pages/UsersPage";
import { WithdrawalDetailsPage } from "./pages/WithdrawalDetailsPage";
import { WithdrawalsPage } from "./pages/WithdrawalsPage";
export function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<AdminRoute />}>
        <Route element={<AdminLayout />}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/plans" element={<PlansPage />} />
          <Route path="/plans/new" element={<PlanFormPage />} />
          <Route path="/plans/:id" element={<PlanFormPage />} />
          <Route path="/users" element={<UsersPage />} />
          <Route path="/users/:id" element={<UserDetailsPage />} />
          <Route path="/deposits" element={<DepositsPage />} />
          <Route path="/deposits/:id" element={<DepositDetailsPage />} />
          <Route path="/withdrawals" element={<WithdrawalsPage />} />
          <Route path="/withdrawals/:id" element={<WithdrawalDetailsPage />} />
          <Route path="/support" element={<SupportPage />} />
          <Route path="/support/:id" element={<SupportDetailsPage />} />
          <Route path="/posts" element={<PostsPage />} />
          <Route path="/posts/new" element={<PostFormPage />} />
          <Route path="/posts/:id" element={<PostFormPage />} />
          <Route path="/audit" element={<AuditPage />} />
        </Route>
      </Route>
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
