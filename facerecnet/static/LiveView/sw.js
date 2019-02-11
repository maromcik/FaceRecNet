/*This code is borrowed from Digital Ocean's tutorial which is released under
Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License.
The code has been modified.
The original code can be found on this website to 12th of February 2019.
https://www.digitalocean.com/community/tutorials/how-to-send-web-push-notifications-from-django-applications*/


// Register event listener for the 'push' event.
self.addEventListener('push', function (event) {
    // Retrieve the textual payload from event.data (a PushMessageData object).
    // Other formats are supported (ArrayBuffer, Blob, JSON), check out the documentation
    // on https://developer.mozilla.org/en-US/docs/Web/API/PushMessageData.
    const eventInfo = event.data.text();
    const data = JSON.parse(eventInfo);
    const head = data.head || 'New Notification 🕺🕺';
    const body = data.body || 'This is default content. Your notification didn\'t have one 🙄🙄';

    // Keep the service worker alive until the notification is created.
    event.waitUntil(
        self.registration.showNotification(head, {
            body: body,
            icon: 'file:///home/user/PycharmProjects/FaceRecNet/facerecnet/static/ring2.png'
        })
    );
});