self.addEventListener("push", (event) => {
  const data = event.data ? event.data.json() : { title: "CrunchTime", body: "Game alert!" };
  event.waitUntil(
    self.registration.showNotification(data.title, {
      body: data.body,
      icon: "/static/icon.png",
      badge: "/static/icon.png",
    })
  );
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  event.waitUntil(clients.openWindow("/"));
});
