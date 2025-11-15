import React from 'react'

interface VCAppShellProps {
  sidebar?: React.ReactNode
  header?: React.ReactNode
  children: React.ReactNode
}

export const VCAppShell: React.FC<VCAppShellProps> = ({ sidebar, header, children }) => (
  <div className="vc-app">
    {sidebar && (
      <aside className="hidden w-64 flex-col border-r border-vc-border bg-[#0A0A10] md:flex">
        <div className="px-5 py-4 font-display text-lg tracking-wide">VibeCraft</div>
        <div className="flex-1 overflow-y-auto">{sidebar}</div>
      </aside>
    )}
    <div className="flex flex-1 flex-col">
      {header && (
        <header className="border-b border-vc-border bg-[rgba(12,12,18,0.92)] backdrop-blur-md">
          <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
            {header}
          </div>
        </header>
      )}
      <main className="vc-app-main">{children}</main>
    </div>
  </div>
)
