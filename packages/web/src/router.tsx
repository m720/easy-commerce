import { createBrowserRouter, RouterProvider } from "react-router-dom"
import RootLayout from "@/components/layout/RootLayout"
import AdminLayout from "@/components/layout/AdminLayout"
import AuthGuard from "@/components/layout/AuthGuard"

// Auth pages
import LoginPage from "@/pages/auth/LoginPage"
import RegisterPage from "@/pages/auth/RegisterPage"

// Shop pages
import HomePage from "@/pages/shop/HomePage"
import ProductListPage from "@/pages/shop/ProductListPage"
import ProductDetailPage from "@/pages/shop/ProductDetailPage"
import CartPage from "@/pages/shop/CartPage"
import CheckoutPage from "@/pages/shop/CheckoutPage"
import OrdersPage from "@/pages/shop/OrdersPage"
import OrderDetailPage from "@/pages/shop/OrderDetailPage"
import WishlistPage from "@/pages/shop/WishlistPage"
import ProfilePage from "@/pages/shop/ProfilePage"

// Admin pages
import DashboardPage from "@/pages/admin/DashboardPage"
import AdminProductsPage from "@/pages/admin/ProductsPage"
import ProductFormPage from "@/pages/admin/ProductFormPage"
import CategoriesPage from "@/pages/admin/CategoriesPage"
import TagsPage from "@/pages/admin/TagsPage"
import AdminOrdersPage from "@/pages/admin/OrdersPage"
import ReturnsPage from "@/pages/admin/ReturnsPage"
import CouponsPage from "@/pages/admin/CouponsPage"
import UsersPage from "@/pages/admin/UsersPage"
import AnalyticsPage from "@/pages/admin/AnalyticsPage"

const router = createBrowserRouter([
  {
    path: "/",
    element: <RootLayout />,
    children: [
      { index: true, element: <HomePage /> },
      { path: "products", element: <ProductListPage /> },
      { path: "products/:id", element: <ProductDetailPage /> },
      { path: "login", element: <LoginPage /> },
      { path: "register", element: <RegisterPage /> },
      {
        path: "cart",
        element: <AuthGuard><CartPage /></AuthGuard>,
      },
      {
        path: "checkout",
        element: <AuthGuard><CheckoutPage /></AuthGuard>,
      },
      {
        path: "orders",
        element: <AuthGuard><OrdersPage /></AuthGuard>,
      },
      {
        path: "orders/:id",
        element: <AuthGuard><OrderDetailPage /></AuthGuard>,
      },
      {
        path: "wishlist",
        element: <AuthGuard><WishlistPage /></AuthGuard>,
      },
      {
        path: "profile",
        element: <AuthGuard><ProfilePage /></AuthGuard>,
      },
    ],
  },
  {
    path: "/admin",
    element: <AuthGuard role="admin"><AdminLayout /></AuthGuard>,
    children: [
      { index: true, element: <DashboardPage /> },
      { path: "products", element: <AdminProductsPage /> },
      { path: "products/new", element: <ProductFormPage /> },
      { path: "products/:id", element: <ProductFormPage /> },
      { path: "categories", element: <CategoriesPage /> },
      { path: "tags", element: <TagsPage /> },
      { path: "orders", element: <AdminOrdersPage /> },
      { path: "returns", element: <ReturnsPage /> },
      { path: "coupons", element: <CouponsPage /> },
      { path: "users", element: <UsersPage /> },
      { path: "analytics", element: <AnalyticsPage /> },
    ],
  },
])

export default function AppRouter() {
  return <RouterProvider router={router} />
}
