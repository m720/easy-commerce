import { Outlet } from "react-router-dom"
import Header from "./Header"
import Footer from "./Footer"
import DevToolbar from "@/components/dev/DevToolbar"

export default function RootLayout() {
  return (
    <div className="flex flex-col min-h-screen bg-white">
      <Header />
      <main className="flex-1">
        <Outlet />
      </main>
      <Footer />
      <DevToolbar />
    </div>
  )
}
