export interface Branch {
  branch_id: string;
  branch_name: string;
  branch_director?: string;
  address?: string;
  region?: string;
}

export interface BranchSummary extends Branch {
  total_outstanding: number;
  total_customers: number;
  total_loans: number;
  npl_ratio: number;
  red_flag_count: number;
}

export interface Customer {
  cif: string;
  customer_name: string;
  customer_type?: string;
  tax_id?: string;
  id_number?: string;
  phone?: string;
  email?: string;
  branch_id?: string;
  segment?: string;
  created_date?: string;
  credit_rating?: string;
}

export interface CustomerListItem extends Customer {
  branch_name?: string;
  total_outstanding: number;
  max_debt_group: number;
  risk_score: number;
  risk_category: string;
}

export interface Loan {
  loan_id: string;
  cif: string;
  branch_id?: string;
  loan_amount: number;
  outstanding_balance: number;
  disbursement_date?: string;
  maturity_date?: string;
  interest_rate?: number;
  loan_purpose?: string;
  loan_category?: string;
  debt_group: number;
  loan_officer?: string;
  status?: string;
}

export interface Transaction {
  txn_id: string;
  loan_id?: string;
  cif: string;
  txn_date?: string;
  txn_type?: string;
  amount: number;
  description?: string;
  channel?: string;
}

export interface OffBalance {
  off_balance_id: string;
  cif: string;
  ob_type?: string;
  amount: number;
  issue_date?: string;
  expiry_date?: string;
  status?: string;
}

export interface RuleHit {
  rule_id: string;
  description: string;
  points: number;
  severity: string;
}

export interface RiskAnalysis {
  total_score: number;
  risk_category: string;
  rule_hits: RuleHit[];
  cic?: CICData;
}

export interface CICData {
  total_debt_other_banks: number;
  debt_group_other_banks: number;
  bad_debt_amount: number;
  number_of_credit_institutions: number;
  has_overdue_history: boolean;
}

export interface TaxStatus {
  tax_id: string;
  company_name?: string;
  status?: string;
  registration_date?: string;
}

export interface InvoiceSummary {
  total: number;
  cancelled: number;
  cancellation_rate: number;
}

export interface SocialInsurance {
  si_id: string;
  tax_id: string;
  report_period?: string;
  declared_employees: number;
  actual_employees: number;
  total_salary_fund: number;
}

export interface MisuseData {
  tax_status?: TaxStatus;
  invoice_summary?: InvoiceSummary;
  si_mismatch?: SocialInsurance;
  logistics_count: number;
}

export interface CustomerDetail {
  customer_info: Customer;
  loans: Loan[];
  off_balance: OffBalance[];
  recent_transactions: Transaction[];
  risk_analysis: RiskAnalysis;
  misuse_data: MisuseData;
}

export interface DashboardKPIs {
  npl_ratio: number;
  group2_ratio: number;
  restructured_ratio: number;
  llcr: number;
  total_outstanding: number;
  total_customers: number;
  total_loans: number;
  red_flag_count: number;
}

export interface TrendDataPoint {
  month: string;
  npl_ratio: number;
  group2_ratio: number;
  total_outstanding: number;
}

export interface TopRedFlag {
  cif: string;
  customer_name: string;
  risk_score: number;
  risk_category: string;
  total_outstanding: number;
  branch_name: string;
  top_rules: string[];
}

export interface PortfolioBreakdown {
  category: string;
  amount: number;
  percentage: number;
}

export interface DebtGroupBreakdown {
  group: number;
  amount: number;
  count: number;
}

export interface BranchDetail {
  branch_info: Branch;
  total_outstanding: number;
  portfolio_breakdown: PortfolioBreakdown[];
  debt_group_breakdown: DebtGroupBreakdown[];
  top_risky_loans: Loan[];
  early_warnings: string[];
}

export interface MisusePattern {
  pattern: string;
  count: number;
  total_amount: number;
}

export interface MisuseOverview {
  total_flagged_outstanding: number;
  total_flagged_cases: number;
  pattern_distribution: MisusePattern[];
}

export interface VendorHubCustomer {
  cif: string;
  customer_name: string;
  outstanding: number;
}

export interface VendorHub {
  vendor_tax_id: string;
  company_name: string;
  connected_customers: number;
  total_amount: number;
  is_suspicious: boolean;
  customer_list: VendorHubCustomer[];
}

export interface Case {
  case_id: string;
  cif: string;
  loan_id?: string;
  created_date?: string;
  status?: string;
  assigned_to?: string;
  description?: string;
  priority?: string;
  audit_log?: string;
  customer_name?: string;
  risk_score?: number;
  risk_category?: string;
}

export interface CaseCreate {
  cif: string;
  loan_id?: string;
  description: string;
  priority: string;
  assigned_to?: string;
}

export interface CaseUpdate {
  status?: string;
  assigned_to?: string;
  description?: string;
  priority?: string;
}

export interface User {
  user_id: string;
  username: string;
  full_name?: string;
  role?: string;
  branch_id?: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
}

export type RiskCategory = 'Green' | 'Amber' | 'Red';
export type CaseStatus = 'todo' | 'in_progress' | 'pending_branch' | 'closed';
export type Priority = 'high' | 'medium' | 'low';
