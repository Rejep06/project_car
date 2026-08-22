import { Navigate, Route, Routes } from "react-router-dom";
import { ProtectedRoute } from "./auth/ProtectedRoute";
import { AccountLayout } from "./components/AccountLayout";
import { PublicLayout } from "./components/PublicLayout";
import { AboutPage } from "./pages/AboutPage";
import { CheckEmailPage } from "./pages/CheckEmailPage";
import { FaqPage } from "./pages/FaqPage";
import { ForgotPasswordPage } from "./pages/ForgotPasswordPage";
import { HomePage } from "./pages/HomePage";
import { HowItWorksPage } from "./pages/HowItWorksPage";
import { LoginPage } from "./pages/LoginPage";
import { LotteriesPage } from "./pages/LotteriesPage";
import { LotteryDetailsPage } from "./pages/LotteryDetailsPage";
import { NewsDetailsPage } from "./pages/NewsDetailsPage";
import { NewsPage } from "./pages/NewsPage";
import { NotFoundPage } from "./pages/NotFoundPage";
import { PersonalDataConsentPage } from "./pages/PersonalDataConsentPage";
import { PlanDetailsPage } from "./pages/PlanDetailsPage";
import { PlansPage } from "./pages/PlansPage";
import { PrivacyPage } from "./pages/PrivacyPage";
import { ProgramRulesPage } from "./pages/ProgramRulesPage";
import { RegisterPage } from "./pages/RegisterPage";
import { ResetPasswordPage } from "./pages/ResetPasswordPage";
import { TermsPage } from "./pages/TermsPage";
import { VerifyEmailPage } from "./pages/VerifyEmailPage";
import { AccountDashboardPage } from "./pages/account/AccountDashboardPage";
import { AccountLotteriesPage } from "./pages/account/AccountLotteriesPage";
import { DepositDetailsPage } from "./pages/account/DepositDetailsPage";
import { DepositsPage } from "./pages/account/DepositsPage";
import { NotificationsPage } from "./pages/account/NotificationsPage";
import { ProfilePage } from "./pages/account/ProfilePage";
import { ReferralsPage } from "./pages/account/ReferralsPage";
import { RewardsPage } from "./pages/account/RewardsPage";
import { SubscriptionDetailsPage } from "./pages/account/SubscriptionDetailsPage";
import { SubscriptionsPage } from "./pages/account/SubscriptionsPage";
import { SupportDetailsPage } from "./pages/account/SupportDetailsPage";
import { SupportPage } from "./pages/account/SupportPage";
import { TransactionsPage } from "./pages/account/TransactionsPage";
import { WalletPage } from "./pages/account/WalletPage";
import { WithdrawalsPage } from "./pages/account/WithdrawalsPage";

export function App() {
  return (
    <Routes>
      <Route element={<PublicLayout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/plans" element={<PlansPage />} />
        <Route path="/plans/:id" element={<PlanDetailsPage />} />
        <Route path="/lotteries" element={<LotteriesPage />} />
        <Route path="/lotteries/:id" element={<LotteryDetailsPage />} />
        <Route path="/news" element={<NewsPage />} />
        <Route path="/news/:slug" element={<NewsDetailsPage />} />
        <Route path="/about" element={<AboutPage />} />
        <Route path="/how-it-works" element={<HowItWorksPage />} />
        <Route path="/faq" element={<FaqPage />} />
        <Route path="/terms" element={<TermsPage />} />
        <Route path="/privacy" element={<PrivacyPage />} />
        <Route path="/program-rules" element={<ProgramRulesPage />} />
        <Route path="/personal-data-consent" element={<PersonalDataConsentPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/check-email" element={<CheckEmailPage />} />
        <Route path="/verify-email" element={<VerifyEmailPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/reset-password" element={<ResetPasswordPage />} />
      </Route>
      <Route element={<ProtectedRoute />}>
        <Route path="/account" element={<AccountLayout />}>
          <Route index element={<AccountDashboardPage />} />
          <Route path="wallet" element={<WalletPage />} />
          <Route path="deposits" element={<DepositsPage />} />
          <Route path="deposits/:id" element={<DepositDetailsPage />} />
          <Route path="withdrawals" element={<WithdrawalsPage />} />
          <Route path="subscriptions" element={<SubscriptionsPage />} />
          <Route
            path="subscriptions/:id"
            element={<SubscriptionDetailsPage />}
          />
          <Route path="rewards" element={<RewardsPage />} />
          <Route path="lotteries" element={<AccountLotteriesPage />} />
          <Route path="notifications" element={<NotificationsPage />} />
          <Route path="referrals" element={<ReferralsPage />} />
          <Route path="transactions" element={<TransactionsPage />} />
          <Route path="support" element={<SupportPage />} />
          <Route path="support/:id" element={<SupportDetailsPage />} />
          <Route path="profile" element={<ProfilePage />} />
        </Route>
      </Route>
      <Route path="/dashboard" element={<Navigate to="/account" replace />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
