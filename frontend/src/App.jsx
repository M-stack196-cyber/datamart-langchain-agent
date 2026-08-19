import { useCallback, useState } from "react";

import AdminDashboard from "./AdminDashboard";
import AdminLogin from "./AdminLogin";
import DtmHomepage from "./DtmHomepage";
import FloatingChat from "./FloatingChat";

import "./dtm-homepage.css";
import "./floating-chat.css";


function PublicWebsite() {
  const [openChat, setOpenChat] = useState(false);

  const requestChatOpen = useCallback(() => {
    setOpenChat(true);
  }, []);

  const handleChatOpened = useCallback(() => {
    setOpenChat(false);
  }, []);

  return (
    <>
      <DtmHomepage onOpenChat={requestChatOpen} />

      <FloatingChat
        externalOpen={openChat}
        onExternalOpenHandled={handleChatOpened}
      />
    </>
  );
}


export default function App() {
  const path = window.location.pathname;

  if (path === "/admin/login") {
    return <AdminLogin />;
  }

  if (
    path === "/admin" ||
    path.startsWith("/admin/")
  ) {
    return <AdminDashboard />;
  }

  return <PublicWebsite />;
}
