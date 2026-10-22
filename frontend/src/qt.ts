/** QWebChannel APIs provided by the bundled Qt resource at runtime. */
export type QtBridge = {
  request(raw: string, callback: (reply: string) => void): void;
  clientReady(callback?: () => void): void;
  pushed: { connect(callback: (raw: string) => void): void };
};
type Channel = { objects: { spike?: QtBridge } };
type ChannelConstructor = new (
  transport: object,
  callback: (channel: Channel) => void,
) => object;

declare global {
  interface Window {
    qt?: { webChannelTransport?: object };
    QWebChannel?: ChannelConstructor;
    __ccBridge?: QtBridge; // Diagnostic hook, equivalent to QWebChannel's exposed QObject.
  }
}
export {};
