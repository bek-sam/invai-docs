-- action_adoption_rate v1 (metrics/definitions/action_adoption_rate.md)
-- Of ranked action insights shown in ready digests whose week ended in the window, the share
-- clicked by anyone (digest_clicks) and the share voted up. Market items also count "done" votes
-- (market_recommendations.vote / adopted_at). Measures whether analytics change what shops do.
WITH shops AS (
  SELECT id AS company_id, slug, timezone FROM companies
  WHERE type = 'shop' AND deleted_at IS NULL AND demo_owner_user_id IS NULL
    AND (settings->>'demoRetiredAt') IS NULL)
SELECT s.slug, i.detector, count(*) AS shown,
  count(*) FILTER (WHERE EXISTS (SELECT 1 FROM digest_clicks c WHERE c.insight_id = i.id)) AS clicked,
  count(*) FILTER (WHERE EXISTS (SELECT 1 FROM digest_feedback fb WHERE fb.insight_id = i.id AND fb.vote = 'up')) AS voted_up,
  count(*) FILTER (WHERE EXISTS (SELECT 1 FROM digest_feedback fb WHERE fb.insight_id = i.id AND fb.vote = 'down')) AS voted_down
FROM shops s JOIN digests d ON d.company_id = s.company_id AND d.status = 'ready'
  AND d.week_end >= :'from'::date AND d.week_end < :'to'::date
JOIN digest_insights i ON i.digest_id = d.id AND i.section = 'action'
GROUP BY 1, 2 ORDER BY 1, 2;
