$(document).ready(function() {
  
  const load_chat = lang => {
    const container = $( "#webchat" );

    // remove the previous chat window, if any
    container.empty();

    // debug - don't preserve state upon page reload
    localStorage.clear();

    // Support TLS-specific URLs, when appropriate.
    if (Env.serverUrl.startsWith("https:")) {
        var ws_scheme = "wss";
    } else {
        var ws_scheme = "ws"
    };

    const socketUrl = Env.serverUrl.replace(/(^\w+:|^)\/\//, ws_scheme + '://');
    const serverUrl = `${Env.serverUrl}`;

    const title = container.attr('data-title');
    const subtitle = container.attr('data-subtitle');

    WebChat.default.init({
      selector: "#webchat",
      interval: 1000, // 1000 ms between each message
      initPayload: "utter_greet",
      customData: { 'lang': lang }, // arbitrary custom data. Stay minimal as this will be added to the socket
      socketUrl: socketUrl,
      socketPath: "/socket.io/",
      title: title,
      subtitle: subtitle,
      inputTextFieldHint: "Type a message...",
      connectingText: "Waiting for server...",
      hideWhenNotConnected: false,  // TODO true
      fullScreenMode: false,
      profileAvatar: serverUrl + "/static/images/avatar.png",
      params: {
        storage: "local"
      }
    });
    WebChat.open();
  };
  // Load the default chat in English
  load_chat('en');

  $("#choice_en").click(function() {
      load_chat('en');
  });

  $("#choice_de").click(function() {
      load_chat('bn');
  });
  // $("#choice_sv").click(function() {
  //     load_chat('sv');
  // });
});
