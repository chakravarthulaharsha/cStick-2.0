import React from "react";
import { Link, useLocation } from "react-router-dom";
import { createPageUrl } from "@/utils";
import { Activity, Plus, Calendar, BarChart3, Edit3, TrendingUp, Upload } from "lucide-react";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarHeader,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";

const navigationItems = [
  {
    title: "Add New Log",
    url: createPageUrl("AddLog"),
    icon: Plus,
  },
  {
    title: "Import CSV",
    url: createPageUrl("ImportCSV"),
    icon: Upload,
  },
  {
    title: "Daily View",
    url: createPageUrl("DailyView"),
    icon: Calendar,
  },
  {
    title: "Monthly Analytics",
    url: createPageUrl("MonthlyAnalytics"),
    icon: TrendingUp,
  },
  {
    title: "Edit Data",
    url: createPageUrl("EditData"),
    icon: Edit3,
  },
  {
    title: "Statistics",
    url: createPageUrl("Statistics"),
    icon: BarChart3,
  },
];

export default function Layout({ children, currentPageName }) {
  const location = useLocation();

  return (
    <SidebarProvider>
      <style>{`
        :root {
          --primary: 186 100% 45%;
          --primary-foreground: 0 0% 100%;
          --secondary: 186 30% 95%;
          --accent: 186 80% 55%;
        }
      `}</style>
      <div className="min-h-screen flex w-full bg-gradient-to-br from-slate-50 to-teal-50">
        <Sidebar className="border-r border-teal-100 bg-white/80 backdrop-blur-sm">
          <SidebarHeader className="border-b border-teal-100 p-6">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-gradient-to-br from-teal-500 to-cyan-600 rounded-2xl flex items-center justify-center shadow-lg">
                <Activity className="w-7 h-7 text-white" />
              </div>
              <div>
                <h2 className="font-bold text-xl text-slate-900">cStick</h2>
                <p className="text-xs text-teal-600 font-medium">Fall Detection</p>
              </div>
            </div>
          </SidebarHeader>
          
          <SidebarContent className="p-3">
            <SidebarGroup>
              <SidebarGroupContent>
                <SidebarMenu>
                  {navigationItems.map((item) => (
                    <SidebarMenuItem key={item.title}>
                      <SidebarMenuButton 
                        asChild 
                        className={`mb-1 rounded-xl transition-all duration-300 ${
                          location.pathname === item.url 
                            ? 'bg-gradient-to-r from-teal-500 to-cyan-600 text-white shadow-md' 
                            : 'hover:bg-teal-50 text-slate-700'
                        }`}
                      >
                        <Link to={item.url} className="flex items-center gap-3 px-4 py-3">
                          <item.icon className="w-5 h-5" />
                          <span className="font-medium">{item.title}</span>
                        </Link>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  ))}
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>
          </SidebarContent>
        </Sidebar>

        <main className="flex-1 flex flex-col">
          <header className="bg-white/80 backdrop-blur-sm border-b border-teal-100 px-6 py-4 md:hidden">
            <div className="flex items-center gap-4">
              <SidebarTrigger className="hover:bg-teal-50 p-2 rounded-lg transition-colors" />
              <h1 className="text-xl font-bold text-slate-900">cStick</h1>
            </div>
          </header>

          <div className="flex-1 overflow-auto">
            {children}
          </div>
        </main>
      </div>
    </SidebarProvider>
  );
}