function deleteNote(visitorId) {
  fetch("/delete-note", {
    method: "POST",
    body: JSON.stringify({ visitorId: visitorId }),
  }).then((_res) => {
    window.location.href = "/";
  });
}
