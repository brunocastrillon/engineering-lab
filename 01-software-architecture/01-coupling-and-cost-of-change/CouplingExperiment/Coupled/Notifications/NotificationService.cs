namespace Coupled.Notifications;

/// <summary>
/// Notifies the customer that an invoice was issued.
/// 
/// It receives the Invoice entity and walks Invoice -> Order -> Customer to find the recipient.
/// the notifications depends on the internals of two other modules to send one email.
/// </summary>
/// <param name="transport"></param>
public sealed class NotificationService(SmtpTransport transport)
{

}