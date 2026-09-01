namespace Coupled.Notifications;

public readonly record struct SentMessage(string Recipient, string Subject, string Body);

/// <summary>
/// Stand-in for an SMTP client.
/// In a real application, this would be a wrapper around an SMTP library, but here it just records the messages that would have been sent.
/// It records what it would have sent so that the scenario stays deterministic and needs no external service.
/// </summary>
public sealed class SmtpTransport
{
    private readonly List<SentMessage> _sent = [];

    public IReadOnlyList<SentMessage> Sent => _sent;

    public void Send(string recipient, string subject, string body) => _sent.Add(new SentMessage(recipient, subject, body));
}