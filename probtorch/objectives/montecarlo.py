from numbers import Number
from torch.nn.functional import softmax
from probtorch.util import sum_log_prob


def elbo(q, p, sample_dim=None, batch_dim=None, alpha=0.1, beta=1.0):
    r"""Calculates a Monte Carlo estimate of the semi-supervised evidence lower
    bound (ELBO)

    .. math::
       E_{q(z | x, y)} \left[
         \log p(x | y, z) - \beta \log \frac{q(z | x,y)}{p(z)}
       \right]
       + \alpha E_{q(z | x)}\left[ \log \frac{q(y, z| x)}{q(z | x)} \right]

    Where the sets of variables :math:`x`, :math:`y` and :math:`z` refer to:

        :math:`x`: The set of conditioned nodes that are present in `p` but
        are not present in `q`.

        :math:`y`: The set of conditioned nodes in `q`.

        :math:`z`: The set of sampled nodes in `q`.

    Importance sampling is used to approximate the expectation over
    :math:`q(z| x,y)`.

    Arguments:
        q(:obj:Trace): The encoder trace.
        p(:obj:Trace): The decoder trace.
        sample_dim(int, optional): The dimension containing individual samples.
        batch_dim(int, optional): The dimension containing batch items.
        alpha(float, default 0.1): Coefficient for the ML term.
        beta(float, default 1.0):  Coefficient for the KL term.
    """
    log_weights = sum_log_prob(q, sample_dim, batch_dim,
                               q.conditioned())
    return (log_like(q, p, sample_dim, batch_dim, log_weights) -
            beta * kl(q, p, sample_dim, batch_dim, log_weights) +
            alpha * ml(q, sample_dim, batch_dim))


def log_like(q, p, sample_dim=None, batch_dim=None, log_weights=None):
    r"""Computes a Monte Carlo estimate of the log-likelihood.

    .. math::
       E_{q(z | x, y)}[\log p(x | y, z)]
       \simeq \frac{1}{S} \frac{1}{B} \sum_{s=1}^S \sum_{b=1}^B
              \log p(x^{(b)} | z^{(s,b)}, y^{(b)})

    Where the sets of variables :math:`x`, :math:`y` and :math:`z` refer to:

        :math:`x`: The set of conditioned nodes that are present in `p` but
        are not present in `q`.

        :math:`y`: The set of conditioned nodes in `q`.

        :math:`z`: The set of sampled nodes in `q`.

    Importance sampling is used to approximate the expectation over
    :math:`q(z| x,y)`.

    Arguments:
        q(:obj:Trace): The encoder trace.
        p(:obj:Trace): The decoder trace.
        sample_dim(int, optional): The dimension containing individual samples.
        batch_dim(int, optional): The dimension containing batch items.
        log_weights(:obj:Variable or number, optional): Log weights for
            samples. Calculated when not specified.
    """
    x = [n for n in p.conditioned() if n not in q]
    log_prob = sum_log_prob(p, sample_dim, batch_dim, x)
    if sample_dim is None:
        return log_prob.mean()
    else:
        if log_weights is None:
            log_weights = sum_log_prob(q, sample_dim, batch_dim,
                                       q.conditioned())
        if isinstance(log_weights, Number):
            return log_prob.mean()
        else:
            weights = softmax(log_weights, 0)
            return (weights * log_prob).sum(0).mean()


def kl(q, p, sample_dim=None, batch_dim=None, log_weights=None):
    r"""Computes a Monte Carlo estimate of the KL divergence.

    .. math::
       E_{q(z | x, y)}\left[ \log \frac{q(z | x,y)}{p(z)} \right]
       \simeq \frac{1}{S} \frac{1}{B} \sum_{s=1}^S \sum_{b=1}^B
       \left[ \log \frac{q(z^{(s,b)} | x^{(b)}, y^{(b)})}
                        {p(z^{(s,b)})} \right]

    Where the sets of variables :math:`x`, :math:`y` and :math:`z` refer to:

        :math:`x`: The set of conditioned nodes that are present in `p` but
        are not present in `q`.

        :math:`y`: The set of conditioned nodes in `q`.

        :math:`z`: The set of sampled nodes in `q`.

    Importance sampling is used to approximate the expectation over
    :math:`q(z| x,y)`.

    Arguments:
        q(:obj:Trace): The encoder trace.
        p(:obj:Trace): The decoder trace.
        sample_dim(int, optional): The dimension containing individual samples.
        batch_dim(int, optional): The dimension containing batch items.
        log_weights(:obj:Variable or number, optional): Log weights for
            samples. Calculated when not specified.
    """
    z = list(q.sampled())
    log_p = sum_log_prob(p, sample_dim, batch_dim, z)
    log_q = sum_log_prob(q, sample_dim, batch_dim, z)
    log_qp = (log_q - log_p)
    if sample_dim is None:
        return log_qp.mean()
    else:
        if log_weights is None:
            log_weights = sum_log_prob(q, sample_dim, batch_dim,
                                       q.conditioned())
        if isinstance(log_weights, Number):
            return log_qp.mean()
        else:
            weights = softmax(log_weights, 0)
            return (weights * log_qp).sum(0).mean()


def ml(q, sample_dim=None, batch_dim=None):
    r"""Computes a Monte Carlo estimate of maximum likelihood encoder objective

    .. math::
       E_{q(z | x)}\left[ \log \frac{q(y, z| x)}{q(z | x)} \right]
       \simeq \frac{1}{S} \frac{1}{B} \sum_{s=1}^S \sum_{b=1}^B
       \left[ \log \frac{q( y^{(b)}, z^{(s,b)} | x^{(b)})}
                        {q(z^{(s,b)} | x^{(b)})} \right]

    Where the sets of variables :math:`x`, :math:`y` and :math:`z` refer to:

        :math:`x`: The set of conditioned nodes that are present in `p` but
        are not present in `q`.

        :math:`y`: The set of conditioned nodes in `q`.

        :math:`z`: The set of sampled nodes in `q`.

    Arguments:
        q(:obj:Trace): The encoder trace.
        p(:obj:Trace): The decoder trace.
        sample_dim(int, optional): The dimension containing individual samples.
        batch_dim(int, optional): The dimension containing batch items.
    """
    log_q = sum_log_prob(q, sample_dim, batch_dim, q.conditioned())
    if isinstance(log_q, Number):
        return log_q
    else:
        return log_q.mean()
