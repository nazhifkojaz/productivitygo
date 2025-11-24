import React from 'react';
import { Outlet } from 'react-router-dom';
import MobileNav from './MobileNav';
import MobileHeader from './MobileHeader';

export default function Layout() {
    return (
        <div className="min-h-screen bg-neo-bg">
            <MobileHeader />
            <div className="pt-16 pb-20 md:pt-0 md:pb-0">
                <Outlet />
            </div>
            <MobileNav />
        </div>
    );
}
