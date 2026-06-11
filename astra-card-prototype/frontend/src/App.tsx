import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { Layout } from "./components/Layout";
import { CardsPage } from "./routes/CardsPage";
import { CreateRoomPage } from "./routes/CreateRoomPage";
import { DemoPage } from "./routes/DemoPage";
import { LandingPage } from "./routes/LandingPage";
import { RoomPage } from "./routes/RoomPage";

const router = createBrowserRouter([{
  path: "/",
  element: <Layout />,
  children: [
    { index: true, element: <LandingPage /> },
    { path: "demo", element: <DemoPage /> },
    { path: "cards", element: <CardsPage /> },
    { path: "room/create", element: <CreateRoomPage /> },
    { path: "room/:roomId", element: <RoomPage /> },
  ],
}]);

export default function App() {
  return <RouterProvider router={router} />;
}
